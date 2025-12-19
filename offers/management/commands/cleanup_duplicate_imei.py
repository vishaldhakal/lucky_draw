from django.core.management.base import BaseCommand
from django.db.models import Count

from offers.models import IMEINO


class Command(BaseCommand):
    help = 'Find and delete duplicate IMEI records where phone_model contains "vivo"'

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Find all IMEI numbers that have duplicates
        duplicate_imeis = (
            IMEINO.objects.values("imei_no")
            .annotate(count=Count("imei_no"))
            .filter(count__gt=1)
        )

        total_duplicates = duplicate_imeis.count()
        deleted_count = 0

        self.stdout.write(f"Found {total_duplicates} IMEI numbers with duplicates\n")

        for item in duplicate_imeis:
            imei_no = item["imei_no"]
            count = item["count"]

            # Get all records with this IMEI number
            records = IMEINO.objects.filter(imei_no=imei_no)

            # Find records where phone_model contains 'vivo' (case-insensitive)
            vivo_records = records.filter(phone_model__icontains="vivo")

            if vivo_records.exists():
                # Delete all but one vivo record (keep the first one)
                records_to_delete = vivo_records[1:]

                if records_to_delete:
                    for record in records_to_delete:
                        if dry_run:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"[DRY RUN] Would delete: IMEI={record.imei_no}, "
                                    f"Model={record.phone_model}, ID={record.id}"
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Deleting: IMEI={record.imei_no}, "
                                    f"Model={record.phone_model}, ID={record.id}"
                                )
                            )
                            record.delete()
                            deleted_count += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\n[DRY RUN] Would delete {deleted_count} duplicate IMEI records"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully deleted {deleted_count} duplicate IMEI records"
                )
            )
