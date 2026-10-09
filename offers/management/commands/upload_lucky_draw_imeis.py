import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from offers.models import IMEINO, LuckyDrawSystem
from offers.services.imei_service import (
    bulk_upload_imeis_from_csv,
    bulk_upload_imeis_with_region_from_file,
)


class Command(BaseCommand):
    help = (
        "Bulk upload IMEI numbers from a CSV or Excel file into a selected Lucky Draw System. "
        "Supports standard IMEI files or files with region (Item, Market Name, IMEI, Region)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--id",
            "--system-id",
            dest="system_id",
            type=int,
            help="Primary Key (ID) of the LuckyDrawSystem.",
        )
        parser.add_argument(
            "--name",
            dest="name",
            type=str,
            help="Exact or partial name of the LuckyDrawSystem to search for.",
        )
        parser.add_argument(
            "-f",
            "--file",
            dest="file_path",
            type=str,
            required=True,
            help="Path to the file containing IMEI numbers (.csv, .xlsx, .xls).",
        )
        parser.add_argument(
            "--with-region",
            dest="with_region",
            action="store_true",
            help="Upload file containing Item, Market Name, IMEI, Region columns.",
        )
        parser.add_argument(
            "--update-existing",
            dest="update_existing",
            action="store_true",
            help="Update phone_model and region for existing IMEI records.",
        )
        parser.add_argument(
            "--batch-size",
            dest="batch_size",
            type=int,
            default=5000,
            help="Number of records to insert per database batch chunk (default: 5000).",
        )
        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="Simulate the upload and display counts without saving to the database.",
        )

    def handle(self, *args, **options):
        system_id = options.get("system_id")
        name = options.get("name")
        file_path = options.get("file_path")
        batch_size = options.get("batch_size")
        dry_run = options.get("dry_run")
        with_region = options.get("with_region")
        update_existing = options.get("update_existing")

        if not os.path.exists(file_path):
            raise CommandError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in [".csv", ".tsv", ".txt", ".xlsx", ".xls"]:
            raise CommandError(f"Unsupported file format '{ext}'. Must be .csv, .xlsx, or .xls.")

        # 1. Resolve LuckyDrawSystem
        if not system_id and not name:
            self.stdout.write(
                self.style.WARNING("No LuckyDrawSystem specified. Available systems:")
            )
            for sys in LuckyDrawSystem.objects.all().order_by("id")[:25]:
                count = IMEINO.objects.filter(lucky_draw_system=sys).count()
                self.stdout.write(
                    f"  [ID: {sys.id}] {sys.name} (Organization: {sys.organization}) - {count} IMEIs"
                )
            raise CommandError("Please specify --id <system_id> or --name <name>.")

        if system_id:
            try:
                lucky_draw = LuckyDrawSystem.objects.get(id=system_id)
            except LuckyDrawSystem.DoesNotExist:
                raise CommandError(
                    f"LuckyDrawSystem with ID {system_id} does not exist."
                )
        else:
            systems = LuckyDrawSystem.objects.filter(name__icontains=name)
            count = systems.count()
            if count == 0:
                raise CommandError(f"No LuckyDrawSystem found matching name: '{name}'.")
            elif count > 1:
                self.stdout.write(
                    self.style.ERROR(
                        f"Multiple LuckyDrawSystems ({count}) match name '{name}':"
                    )
                )
                for s in systems:
                    self.stdout.write(f"  [ID: {s.id}] {s.name}")
                raise CommandError("Please specify the exact system by --id.")
            lucky_draw = systems.first()

        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(
            self.style.NOTICE(
                f"Lucky Draw System : {lucky_draw.name} (ID: {lucky_draw.id})"
            )
        )
        self.stdout.write(
            self.style.NOTICE(f"Organization      : {lucky_draw.organization}")
        )
        self.stdout.write(f"File Path         : {file_path}")
        self.stdout.write(f"With Region       : {with_region or ext in ['.xlsx', '.xls']}")
        self.stdout.write(f"Update Existing   : {update_existing}")
        self.stdout.write(f"Batch Size        : {batch_size}")
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Mode              : DRY RUN (no database changes will be saved)"
                )
            )
        self.stdout.write(self.style.NOTICE("=" * 60))

        use_region_uploader = with_region or ext in [".xlsx", ".xls"]

        with open(file_path, "rb") as f:
            if dry_run:
                with transaction.atomic():
                    if use_region_uploader:
                        result = bulk_upload_imeis_with_region_from_file(
                            lucky_draw_system_id=lucky_draw.id,
                            file_obj=f,
                            batch_size=batch_size,
                            update_existing=update_existing,
                        )
                    else:
                        result = bulk_upload_imeis_from_csv(
                            lucky_draw_system_id=lucky_draw.id,
                            file_obj=f,
                            batch_size=batch_size,
                        )
                    transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING("[DRY RUN COMPLETE] Simulated metrics:")
                )
            else:
                if use_region_uploader:
                    result = bulk_upload_imeis_with_region_from_file(
                        lucky_draw_system_id=lucky_draw.id,
                        file_obj=f,
                        batch_size=batch_size,
                        update_existing=update_existing,
                    )
                else:
                    result = bulk_upload_imeis_from_csv(
                        lucky_draw_system_id=lucky_draw.id,
                        file_obj=f,
                        batch_size=batch_size,
                    )
                self.stdout.write(
                    self.style.SUCCESS("[SUCCESS] IMEI upload completed!")
                )

        self.stdout.write(
            f"  Total Rows in File       : {result['total_rows_processed']:,}"
        )
        self.stdout.write(
            f"  Unique IMEIs in File     : {result['unique_rows_in_file']:,}"
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"  Newly Inserted           : {result['inserted_count']:,}"
            )
        )
        self.stdout.write(
            f"  File Duplicates Skipped  : {result['file_duplicates_count']:,}"
        )
        self.stdout.write(
            f"  Already in DB Skipped    : {result['already_existing_count']:,}"
        )
        self.stdout.write(
            self.style.NOTICE(
                f"  Total Skipped            : {result['skipped_count']:,}"
            )
        )
