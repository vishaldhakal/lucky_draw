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
