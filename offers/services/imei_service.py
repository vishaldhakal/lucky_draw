import csv
import io
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
        text_stream = io.TextIOWrapper(file_obj.file, encoding="utf-8-sig", errors="replace")
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
    first_col = first_row[0].strip().strip('"').strip("'").strip() if len(first_row) > 0 else ""
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
                    IMEINO.objects.bulk_create(batch, batch_size=batch_size, ignore_conflicts=True)
                    if progress_callback:
                        progress_callback(len(seen_in_file), total_rows_processed)
                    batch = []

        if batch:
            IMEINO.objects.bulk_create(batch, batch_size=batch_size, ignore_conflicts=True)
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

