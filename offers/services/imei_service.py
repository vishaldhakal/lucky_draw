import csv
import io
import os
from typing import Any, Callable, Dict, Optional

from django.core.exceptions import ValidationError
from django.db import transaction

from offers.models import IMEINO, LuckyDrawSystem


def delete_imeis_for_lucky_draw_system(
    lucky_draw_system_id: int,
    organization: Optional[Any] = None,
    only_unused: bool = False,
    batch_size: int = 5000,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, Any]:
    """
    Deletes all (or unused) IMEI records for a specified LuckyDrawSystem.

    Optimized for high-volume deletion (e.g. 40,000+ records) using chunked batching
    to avoid memory exhaustion, excessive database lock durations, and connection timeouts.

    :param lucky_draw_system_id: Primary key of LuckyDrawSystem.
    :param organization: Optional organization instance for multi-tenant isolation.
    :param only_unused: If True, only deletes IMEIs where used=False.
    :param batch_size: Number of records to delete per transaction chunk. If 0, deletes in a single query.
    :param progress_callback: Optional callback receiving (deleted_so_far, total_to_delete).
    :return: Dictionary containing execution statistics.
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

    base_qs = IMEINO.objects.filter(lucky_draw_system=lucky_draw)
    if only_unused:
        base_qs = base_qs.filter(used=False)

    total_records = base_qs.count()
    if total_records == 0:
        return {
            "lucky_draw_system_id": lucky_draw.id,
            "lucky_draw_system_name": lucky_draw.name,
            "total_found": 0,
            "deleted_count": 0,
            "only_unused": only_unused,
            "batch_size": batch_size,
            "message": f"No IMEI records found for '{lucky_draw.name}'.",
        }

    # If batch_size <= 0, perform direct single-query deletion
    if not batch_size or batch_size <= 0:
        with transaction.atomic():
            deleted_count, _ = base_qs.delete()
        if progress_callback:
            progress_callback(deleted_count, total_records)
        return {
            "lucky_draw_system_id": lucky_draw.id,
            "lucky_draw_system_name": lucky_draw.name,
            "total_found": total_records,
            "deleted_count": deleted_count,
            "only_unused": only_unused,
            "batch_size": 0,
            "message": f"Successfully deleted {deleted_count} IMEI numbers in a single operation.",
        }

    # Chunked batch deletion to prevent OOM, long transaction locks, and connection timeouts
    total_deleted = 0
    while True:
        # Retrieve only a batch of primary keys
        batch_ids = list(base_qs.values_list("id", flat=True)[:batch_size])
        if not batch_ids:
            break

        with transaction.atomic():
            deleted_count, _ = IMEINO.objects.filter(id__in=batch_ids).delete()
            total_deleted += deleted_count

        if progress_callback:
            progress_callback(total_deleted, total_records)

    return {
        "lucky_draw_system_id": lucky_draw.id,
        "lucky_draw_system_name": lucky_draw.name,
        "total_found": total_records,
        "deleted_count": total_deleted,
        "only_unused": only_unused,
        "batch_size": batch_size,
        "message": f"Successfully deleted {total_deleted} IMEI numbers for '{lucky_draw.name}' in batches of {batch_size}.",
    }


def bulk_upload_imeis_from_csv(
    lucky_draw_system_id: int,
    file_obj: Any,
    batch_size: int = 5000,
    organization: Optional[Any] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, Any]:
    """
    Bulk upload IMEI numbers from a CSV file.

    Optimized for high-volume uploads (50,000+ records) using:
    1. Line-by-line streamed file decoding (avoids monolithic in-memory string copies).
    2. Automatic UTF-8 BOM handling and defensive quote/whitespace stripping.
    3. Intelligent header row detection to prevent dropping valid records.
    4. Fast O(1) in-memory deduplication set to prevent intra-file duplicate inserts.
    5. Chunked PostgreSQL bulk_create with ignore_conflicts=True inside an atomic transaction.

    :param lucky_draw_system_id: Primary key of LuckyDrawSystem.
    :param file_obj: Uploaded file object or file-like stream.
    :param batch_size: Number of records to insert per database batch chunk (default: 5000).
    :param organization: Optional organization instance for multi-tenant isolation.
    :param progress_callback: Optional callback receiving (processed_count, total_so_far).
    :return: Dictionary containing upload metrics and execution statistics.
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
        raise ValidationError("CSV file is required.")

    file_name = getattr(file_obj, "name", "")
    if file_name and not file_name.lower().endswith(".csv"):
        raise ValidationError("Invalid file format. Please upload a CSV file.")

    # Rewind file pointer if supported
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)

    # Wrap the file in a streaming TextIOWrapper with utf-8-sig to automatically strip BOM
    if isinstance(file_obj, (io.TextIOBase, io.StringIO)):
        text_stream = file_obj
    elif hasattr(file_obj, "file"):
        text_stream = io.TextIOWrapper(
            file_obj.file, encoding="utf-8-sig", errors="replace"
        )
    else:
        text_stream = io.TextIOWrapper(file_obj, encoding="utf-8-sig", errors="replace")

    reader = csv.reader(text_stream, delimiter=",")

    try:
        first_row = next(reader, None)
    except Exception as e:
        raise ValidationError(f"Error reading CSV file: {str(e)}")

    if first_row is None:
        raise ValidationError("The uploaded CSV file is empty.")

    # Intelligent header detection:
    # A header row contains keywords like "imei", "serial", "model", or has no digits
    first_col = (
        first_row[0].strip().strip('"').strip("'").strip() if len(first_row) > 0 else ""
    )
    first_col_lower = first_col.lower()
    is_header = (
        not any(c.isdigit() for c in first_col)
        or "imei" in first_col_lower
        or "serial" in first_col_lower
        or "model" in first_col_lower
        or "header" in first_col_lower
    )

    seen_in_file = set()
    total_rows_processed = 0
    file_duplicates_count = 0
    batch = []

    def parse_row(row):
        nonlocal total_rows_processed, file_duplicates_count
        if not row or not row[0]:
            return None

        # Cleanly strip surrounding whitespace and stray quote characters
        imei_val = row[0].strip().strip('"').strip("'").strip()
        if not imei_val:
            return None

        model_val = ""
        if len(row) > 1 and row[1]:
            model_val = row[1].strip().strip('"').strip("'").strip()

        # Enforce model max_length constraint safely
        if len(imei_val) > 400:
            imei_val = imei_val[:400]
        if len(model_val) > 400:
            model_val = model_val[:400]

        total_rows_processed += 1

        if imei_val in seen_in_file:
            file_duplicates_count += 1
            return None

        seen_in_file.add(imei_val)

        return IMEINO(
            lucky_draw_system=lucky_draw,
            imei_no=imei_val,
            phone_model=model_val,
            used=False,
        )

    # If first row was actual data (not a header), parse it first
    if not is_header:
        obj = parse_row(first_row)
        if obj:
            batch.append(obj)

    initial_count = IMEINO.objects.count()

    # Process all rows in chunks inside an atomic transaction for maximum speed and integrity
    with transaction.atomic():
        for row in reader:
            obj = parse_row(row)
            if obj:
                batch.append(obj)
                if len(batch) >= batch_size:
                    IMEINO.objects.bulk_create(
                        batch, batch_size=batch_size, ignore_conflicts=True
                    )
                    if progress_callback:
                        progress_callback(len(seen_in_file), total_rows_processed)
                    batch = []

        if batch:
            IMEINO.objects.bulk_create(
                batch, batch_size=batch_size, ignore_conflicts=True
            )
            if progress_callback:
                progress_callback(len(seen_in_file), total_rows_processed)
            batch = []

    if total_rows_processed == 0:
        raise ValidationError("No valid data rows found in the CSV file.")

    final_count = IMEINO.objects.count()
    inserted_count = final_count - initial_count
    unique_in_file_count = len(seen_in_file)
    already_existing_in_db_count = max(0, unique_in_file_count - inserted_count)
    total_skipped_count = file_duplicates_count + already_existing_in_db_count

    return {
        "message": "IMEI numbers uploaded successfully",
        "lucky_draw_system_id": lucky_draw.id,
        "lucky_draw_system_name": lucky_draw.name,
        "total_rows_processed": total_rows_processed,
        "unique_rows_in_file": unique_in_file_count,
        "inserted_count": inserted_count,
        "skipped_count": total_skipped_count,
        "file_duplicates_count": file_duplicates_count,
        "already_existing_count": already_existing_in_db_count,
        "batch_size": batch_size,
    }


def bulk_upload_imeis_with_region_from_file(
    lucky_draw_system_id: int,
    file_obj: Any,
    batch_size: int = 5000,
    update_existing: bool = False,
    organization: Optional[Any] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Dict[str, Any]:
    """
    Bulk upload IMEI numbers with region from CSV, TSV, or Excel (.xlsx, .xls) files.

    Expected columns in source file:
      - Item: Internal model/item code (e.g. 'SM-A155F', 'V2310')
      - Market Name: Commercial market name (e.g. 'Galaxy A15', 'Vivo Y27s')
      - IMEI: 15-digit IMEI number
      - Region: Geographical or branch region (e.g. 'Kathmandu', 'Pokhara')

    Data mapping:
      - phone_model: Formatted as "Market Name (Item)"
      - imei_no: Cleaned IMEI string
      - region: Region string (or None if empty)
      - lucky_draw_system: Selected LuckyDrawSystem
      - used: False

    :param lucky_draw_system_id: Primary key of LuckyDrawSystem.
    :param file_obj: Uploaded file or file-like stream.
    :param batch_size: Number of records to insert per database batch chunk (default: 5000).
    :param update_existing: If True, updates phone_model and region for existing IMEIs.
    :param organization: Optional organization instance for multi-tenant isolation.
    :param progress_callback: Optional callback receiving (processed_count, total_so_far).
    :return: Dictionary containing execution statistics and metrics.
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

    file_name = getattr(file_obj, "name", "")
    ext = os.path.splitext(file_name)[1].lower() if file_name else ".csv"
    if ext not in [".csv", ".tsv", ".txt", ".xlsx", ".xls"]:
        raise ValidationError(
            "Invalid file format. Please upload a CSV (.csv) or Excel (.xlsx, .xls) file."
        )

    # Rewind file pointer if supported
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)

    rows_iterator = None

    if ext in [".csv", ".tsv", ".txt"]:
        if isinstance(file_obj, (io.TextIOBase, io.StringIO)):
            text_stream = file_obj
        elif hasattr(file_obj, "file"):
            text_stream = io.TextIOWrapper(
                file_obj.file, encoding="utf-8-sig", errors="replace"
            )
        else:
            text_stream = io.TextIOWrapper(
                file_obj, encoding="utf-8-sig", errors="replace"
            )

        sample = text_stream.read(4096)
        if hasattr(text_stream, "seek"):
            text_stream.seek(0)
        delimiter = (
            "\t" if ("\t" in sample and sample.count("\t") > sample.count(",")) else ","
        )
        rows_iterator = csv.reader(text_stream, delimiter=delimiter)

    elif ext == ".xlsx":
        import openpyxl

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

    def clean_str(val: Any) -> str:
        if val is None:
            return ""
        s = str(val).strip()
        if s.lower() == "none":
            return ""
        return s.strip('"').strip("'").strip()

    def clean_imei(val: Any) -> str:
        if val is None:
            return ""
        if isinstance(val, float):
            if val.is_integer():
                return str(int(val)).strip()
            return f"{val:.0f}".strip()
        if isinstance(val, int):
            return str(val).strip()
        s = str(val).strip().strip('"').strip("'").strip()
        if s.endswith(".0") and s[:-2].isdigit():
            s = s[:-2]
        return s

    imei_idx = None
    model_idx = None
    region_idx = None

    for idx, cell in enumerate(first_row):
        if cell is None:
            continue
        c = str(cell).strip().lower()
        if not c:
            continue
        if ("imei" in c or "serial" in c) and imei_idx is None:
            imei_idx = idx
        elif (
            "model" in c
            or "item" in c
            or "market" in c
            or "product" in c
            or "device" in c
            or "phone" in c
        ) and model_idx is None:
            model_idx = idx
        elif (
            "region" in c
            or "area" in c
            or "zone" in c
            or "branch" in c
            or "location" in c
        ) and region_idx is None:
            region_idx = idx

    first_row_joined = " ".join([str(c).lower() for c in first_row if c is not None])
    is_header = any(
        k in first_row_joined
        for k in [
            "imei",
            "serial",
            "model",
            "region",
            "area",
            "zone",
            "branch",
            "item",
            "market",
        ]
    ) or not any(any(ch.isdigit() for ch in str(c)) for c in first_row if c is not None)

    # Defaults: 1st column is IMEI, 2nd is Model Name, 3rd is Region
    if imei_idx is None and model_idx is None:
        imei_idx = 0
        model_idx = 1
        region_idx = 2
    else:
        if imei_idx is None:
            imei_idx = 0 if model_idx != 0 else 1
        if model_idx is None:
            model_idx = 1 if imei_idx != 1 else 0
        if region_idx is None:
            region_idx = 2

    # If first row is data without header, check if col 0 was Model Name and col 1 was IMEI
    if not is_header and len(first_row) > 1:
        c0 = clean_str(first_row[0])
        c1 = clean_str(first_row[1])
        if (
            any(ch.isdigit() for ch in c1)
            and len(c1) >= 8
            and not any(ch.isdigit() for ch in c0)
        ):
            model_idx = 0
            imei_idx = 1

    seen_in_file = set()
    total_rows_processed = 0
    file_duplicates_count = 0
    batch = []

    def parse_and_create_instance(row):
        nonlocal total_rows_processed, file_duplicates_count
        if not row:
            return None

        imei_raw = row[imei_idx] if len(row) > imei_idx else None
        imei_val = clean_imei(imei_raw)
        if not imei_val or imei_val.lower() in ("imei", "imei_no", "imei no", "serial"):
            return None

        model_val = clean_str(row[model_idx]) if len(row) > model_idx else ""
        region_val = clean_str(row[region_idx]) if len(row) > region_idx else ""

        # Model name saved directly to phone_model (no combining of columns)
        phone_model = model_val

        if len(imei_val) > 400:
            imei_val = imei_val[:400]
        if len(phone_model) > 400:
            phone_model = phone_model[:400]
        if len(region_val) > 400:
            region_val = region_val[:400]

        total_rows_processed += 1

        if imei_val in seen_in_file:
            file_duplicates_count += 1
            return None

        seen_in_file.add(imei_val)

        return IMEINO(
            lucky_draw_system=lucky_draw,
            imei_no=imei_val,
            phone_model=phone_model,
            region=region_val if region_val else None,
            used=False,
        )

    if not is_header:
        obj = parse_and_create_instance(first_row)
        if obj:
            batch.append(obj)

    initial_count = IMEINO.objects.count()

    with transaction.atomic():
        for row in rows_iterator:
            obj = parse_and_create_instance(row)
            if obj:
                batch.append(obj)
                if len(batch) >= batch_size:
                    if update_existing:
                        IMEINO.objects.bulk_create(
                            batch,
                            batch_size=batch_size,
                            update_conflicts=True,
                            unique_fields=["imei_no"],
                            update_fields=[
                                "phone_model",
                                "region",
                                "lucky_draw_system",
                            ],
                        )
                    else:
                        IMEINO.objects.bulk_create(
                            batch,
                            batch_size=batch_size,
                            ignore_conflicts=True,
                        )
                    if progress_callback:
                        progress_callback(len(seen_in_file), total_rows_processed)
                    batch = []

        if batch:
            if update_existing:
                IMEINO.objects.bulk_create(
                    batch,
                    batch_size=batch_size,
                    update_conflicts=True,
                    unique_fields=["imei_no"],
                    update_fields=["phone_model", "region", "lucky_draw_system"],
                )
            else:
                IMEINO.objects.bulk_create(
                    batch,
                    batch_size=batch_size,
                    ignore_conflicts=True,
                )
            if progress_callback:
                progress_callback(len(seen_in_file), total_rows_processed)
            batch = []

    if total_rows_processed == 0:
        raise ValidationError("No valid data rows found in the uploaded file.")

    final_count = IMEINO.objects.count()
    inserted_count = final_count - initial_count
    unique_in_file_count = len(seen_in_file)
    already_existing_in_db_count = max(0, unique_in_file_count - inserted_count)
    total_skipped_count = file_duplicates_count + (
        0 if update_existing else already_existing_in_db_count
    )

    message = (
        f"Successfully processed {unique_in_file_count} IMEI numbers "
        f"({inserted_count} newly inserted, {already_existing_in_db_count} updated)."
        if update_existing
        else f"Successfully uploaded {inserted_count} IMEI numbers with region."
    )

    return {
        "message": message,
        "lucky_draw_system_id": lucky_draw.id,
        "lucky_draw_system_name": lucky_draw.name,
        "total_rows_processed": total_rows_processed,
        "unique_rows_in_file": unique_in_file_count,
        "inserted_count": inserted_count,
        "updated_count": already_existing_in_db_count if update_existing else 0,
        "skipped_count": total_skipped_count,
        "file_duplicates_count": file_duplicates_count,
        "already_existing_count": already_existing_in_db_count,
        "batch_size": batch_size,
    }
