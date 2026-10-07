import csv
import io
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from django.core.exceptions import ValidationError
from django.db import transaction

from offers.models import FixOffer, GiftItem, LuckyDrawSystem


def clean_string_value(val: Any) -> str:
    """
    Cleans cell values from CSV or Excel files.
    Handles float scientific notations, integer conversions (e.g. 123456789.0 -> 123456789),
    and strips surrounding whitespace and stray quote marks.
    """
    if val is None:
        return ""
    if isinstance(val, float):
        if val.is_integer():
            val = int(val)
        else:
            val = f"{val:.0f}"
    val_str = str(val).strip().strip('"').strip("'").strip()
    if val_str.endswith(".0"):
        val_str = val_str[:-2].strip()
    return val_str


def is_header_row(row: Sequence[Any]) -> bool:
    """
    Detects whether a row looks like a table header.
    """
    if not row:
        return False
    row_strs = [str(c).strip().lower() for c in row if c is not None and str(c).strip()]
    if not row_strs:
        return False

    header_keywords = (
        "imei",
        "serial",
        "phone",
        "mobile",
        "contact",
        "header",
        "model",
        "s.n",
        "sn",
        "remarks",
        "item",
    )
    for s in row_strs:
        if any(kw in s for kw in header_keywords):
            return True

    # If the first cell has alphabets and no digits at all, it's typically a header label
    first_cell = row_strs[0]
    if not any(c.isdigit() for c in first_cell):
        return True

    return False


def parse_imeis_from_file(
    file_obj: Any, filename: str
) -> Tuple[List[str], Dict[str, str], int, int]:
    """
    Extracts unique IMEI numbers and optional phone numbers from CSV or Excel (.xlsx, .xls) files.

    :param file_obj: File-like object.
    :param filename: Original filename to determine parsing engine.
    :return: (unique_imeis, phone_map, total_rows_processed, file_duplicates_count)
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        raise ValidationError("Unsupported file format. Please upload a CSV (.csv) or Excel (.xlsx, .xls) file.")

    # Rewind file pointer
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)

    rows_iterator = None

    if ext == ".csv":
        if isinstance(file_obj, (io.TextIOBase, io.StringIO)):
            text_stream = file_obj
        elif hasattr(file_obj, "file"):
            text_stream = io.TextIOWrapper(file_obj.file, encoding="utf-8-sig", errors="replace")
        else:
            text_stream = io.TextIOWrapper(file_obj, encoding="utf-8-sig", errors="replace")
        rows_iterator = csv.reader(text_stream, delimiter=",")

    elif ext == ".xlsx":
        import openpyxl

        # Support InMemoryUploadedFile or TemporaryUploadedFile or file path
        raw_file = getattr(file_obj, "file", file_obj)
        try:
            wb = openpyxl.load_workbook(raw_file, read_only=True, data_only=True)
            sheet = wb.active
            rows_iterator = sheet.iter_rows(values_only=True)
        except Exception as e:
            raise ValidationError(f"Unable to read Excel (.xlsx) file: {str(e)}")

    elif ext == ".xls":
        import xlrd

        try:
            raw_content = file_obj.read() if hasattr(file_obj, "read") else None
            book = xlrd.open_workbook(file_contents=raw_content)
            sheet = book.sheet_by_index(0)
            rows_iterator = (sheet.row_values(r) for r in range(sheet.nrows))
        except Exception as e:
            raise ValidationError(f"Unable to read legacy Excel (.xls) file: {str(e)}")

    if rows_iterator is None:
        raise ValidationError("Failed to initialize file reader.")

    try:
        first_row = next(rows_iterator, None)
    except Exception as e:
        raise ValidationError(f"Error reading file content: {str(e)}")

    if first_row is None:
        raise ValidationError("The uploaded file is empty.")

    imei_col_idx = 0
    phone_col_idx = None
    has_header = is_header_row(first_row)

    if has_header:
        for idx, cell in enumerate(first_row):
            c = str(cell).strip().lower()
            if "imei" in c or "serial" in c:
                imei_col_idx = idx
            elif "phone" in c or "mobile" in c or "contact" in c:
                phone_col_idx = idx

    seen_imeis = set()
    unique_imeis = []
    phone_map = {}
    total_rows_processed = 0
    file_duplicates_count = 0

    def process_single_row(row):
        nonlocal total_rows_processed, file_duplicates_count
        if not row:
            return

        # Extract IMEI candidate
        raw_imei = row[imei_col_idx] if len(row) > imei_col_idx else None
        imei_val = clean_string_value(raw_imei)

        # Fallback check if first column was an integer index like 1, 2, 3 and second column is IMEI
        if not has_header and len(row) > 1 and len(imei_val) <= 5 and imei_val.isdigit():
            alt_val = clean_string_value(row[1])
            if len(alt_val) >= 10:
                imei_val = alt_val

        if not imei_val:
            return

        # Enforce max_length safely
        if len(imei_val) > 400:
            imei_val = imei_val[:400]

        total_rows_processed += 1

        if imei_val in seen_imeis:
            file_duplicates_count += 1
            return

        seen_imeis.add(imei_val)
        unique_imeis.append(imei_val)

        # Extract optional phone number
        phone_val = ""
        if phone_col_idx is not None and len(row) > phone_col_idx:
            phone_val = clean_string_value(row[phone_col_idx])
        elif len(row) > 1 and imei_col_idx != 1:
            candidate_phone = clean_string_value(row[1])
            if 7 <= len(candidate_phone) <= 15 and candidate_phone.isdigit():
                phone_val = candidate_phone

        if phone_val:
            phone_map[imei_val] = phone_val[:20]

    # Process first row if it was valid data instead of a header
    if not has_header:
        process_single_row(first_row)

    for row in rows_iterator:
        process_single_row(row)

    return unique_imeis, phone_map, total_rows_processed, file_duplicates_count


def bulk_create_fix_offers_from_file(
    lucky_draw_system_id: int,
    file_obj: Any,
    gift_ids: List[int],
    quantity: int = 1,
    organization: Optional[Any] = None,
    replace_existing: bool = True,
    batch_size: int = 2000,
) -> Dict[str, Any]:
    """
    Bulk creates or updates FixOffer records from an uploaded CSV or Excel file
    and associates the specified gift item(s) with each IMEI.

    Optimized for high performance using:
    1. Fast row parsing and normalization for CSV, XLSX, and XLS formats.
    2. O(1) in-memory deduplication across rows in the uploaded file.
    3. Bulk querying existing FixOffer records to prevent duplicates and support clean updates.
    4. Chunked PostgreSQL bulk_create for new FixOffers and bulk_create for the M2M intermediate through table.
    5. Atomic transaction ensuring all-or-nothing database integrity.

    :param lucky_draw_system_id: Primary key of LuckyDrawSystem.
    :param file_obj: Uploaded file object.
    :param gift_ids: List of GiftItem IDs to attach to the fix offers.
    :param quantity: Quantity of wins available for each IMEI (default 1).
    :param organization: Optional organization for multi-tenant isolation.
    :param replace_existing: If True, updates existing FixOffers for the same IMEI with the selected gift.
    :param batch_size: Number of records to insert per database batch chunk (default 2000).
    :return: Dictionary containing execution statistics and summary.
    """
    qs_system = LuckyDrawSystem.objects.all()
    if organization is not None:
        qs_system = qs_system.filter(organization=organization)

    try:
        lucky_draw = qs_system.get(id=lucky_draw_system_id)
    except LuckyDrawSystem.DoesNotExist:
        raise ValidationError(
            f"LuckyDrawSystem with ID {lucky_draw_system_id} does not exist or you do not have permission to access it."
        )

    if not file_obj:
        raise ValidationError("File is required.")

    if not gift_ids:
        raise ValidationError("At least one gift must be selected.")

    # Validate selected gifts belong to this lucky draw system
    gifts = list(GiftItem.objects.filter(id__in=gift_ids, lucky_draw_system=lucky_draw))
    if not gifts:
        raise ValidationError("None of the selected gifts belong to this Lucky Draw System.")

    valid_gift_ids = [g.id for g in gifts]

    # Parse rows from file
    filename = getattr(file_obj, "name", "file.csv")
    unique_imeis, phone_map, total_rows_processed, file_duplicates_count = parse_imeis_from_file(
        file_obj=file_obj, filename=filename
    )

    if not unique_imeis:
        raise ValidationError("No valid IMEI numbers found in the uploaded file.")

    ThroughModel = FixOffer.gift.through

    created_count = 0
    updated_count = 0
    skipped_existing_count = 0

    with transaction.atomic():
        # Check existing FixOffers for these IMEIs in this lucky draw system
        existing_offers_qs = FixOffer.objects.filter(
            lucky_draw_system=lucky_draw,
            imei_no__in=unique_imeis,
        )
        existing_offers_dict = {fo.imei_no: fo for fo in existing_offers_qs}

        if existing_offers_dict:
            existing_ids = [fo.id for fo in existing_offers_dict.values()]
            if replace_existing:
                # Update quantity in bulk
                FixOffer.objects.filter(id__in=existing_ids).update(quantity=quantity)

                # Reset and assign selected gifts on through table
                ThroughModel.objects.filter(fixoffer_id__in=existing_ids).delete()
                through_to_create = [
                    ThroughModel(fixoffer_id=fo_id, giftitem_id=g_id)
                    for fo_id in existing_ids
                    for g_id in valid_gift_ids
                ]
                ThroughModel.objects.bulk_create(through_to_create, ignore_conflicts=True)
                updated_count = len(existing_ids)
            else:
                skipped_existing_count = len(existing_ids)

        # Determine brand new IMEIs to insert
        new_imeis = [imei for imei in unique_imeis if imei not in existing_offers_dict]

        if new_imeis:
            for i in range(0, len(new_imeis), batch_size):
                chunk_imeis = new_imeis[i : i + batch_size]
                batch_objs = [
                    FixOffer(
                        lucky_draw_system=lucky_draw,
                        imei_no=imei,
                        phone_number=phone_map.get(imei) or None,
                        quantity=quantity,
                    )
                    for imei in chunk_imeis
                ]
                created_instances = FixOffer.objects.bulk_create(batch_objs)

                # Retrieve primary keys (auto-populated in PostgreSQL Django 5.1, or queried if fallback needed)
                if created_instances and getattr(created_instances[0], "id", None):
                    chunk_fo_ids = [fo.id for fo in created_instances]
                else:
                    chunk_fo_ids = list(
                        FixOffer.objects.filter(
                            lucky_draw_system=lucky_draw,
                            imei_no__in=chunk_imeis,
                        ).values_list("id", flat=True)
                    )

                through_records = [
                    ThroughModel(fixoffer_id=fo_id, giftitem_id=g_id)
                    for fo_id in chunk_fo_ids
                    for g_id in valid_gift_ids
                ]
                ThroughModel.objects.bulk_create(through_records, ignore_conflicts=True)
                created_count += len(chunk_fo_ids)

    total_skipped_count = file_duplicates_count + skipped_existing_count

    return {
        "message": "Fix offers created successfully from file.",
        "lucky_draw_system_id": lucky_draw.id,
        "lucky_draw_system_name": lucky_draw.name,
        "selected_gifts": [
            {"id": g.id, "name": g.name, "category": g.category} for g in gifts
        ],
        "quantity": quantity,
        "total_rows_processed": total_rows_processed,
        "unique_imeis_in_file": len(unique_imeis),
        "created_count": created_count,
        "updated_count": updated_count,
        "skipped_count": total_skipped_count,
        "file_duplicates_count": file_duplicates_count,
        "batch_size": batch_size,
    }
