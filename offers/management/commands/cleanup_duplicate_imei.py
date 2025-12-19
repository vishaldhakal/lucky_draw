from django.core.management.base import BaseCommand

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

        # Get all IMEI records
        all_imeis = IMEINO.objects.all()

        # Group by normalized IMEI (stripped)
        imei_groups = {}
        for record in all_imeis:
            normalized_imei = record.imei_no.strip()
            if normalized_imei not in imei_groups:
                imei_groups[normalized_imei] = []
            imei_groups[normalized_imei].append(record)

        # Find groups with duplicates
        duplicate_groups = {k: v for k, v in imei_groups.items() if len(v) > 1}

        total_duplicates = len(duplicate_groups)
        deleted_count = 0

        self.stdout.write(f"Found {total_duplicates} IMEI numbers with duplicates\n")

        for normalized_imei, records in duplicate_groups.items():
            count = len(records)

            self.stdout.write(
                self.style.NOTICE(
                    f"\nProcessing IMEI '{normalized_imei}' ({count} duplicates)"
                )
            )

            # Find records where phone_model contains 'vivo' (case-insensitive)
            vivo_records = [r for r in records if "vivo" in r.phone_model.lower()]
            non_vivo_records = [
                r for r in records if "vivo" not in r.phone_model.lower()
            ]

            if vivo_records:
                # Delete ALL vivo records when duplicates exist
                for record in vivo_records:
                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  [DRY RUN] Would delete: IMEI='{record.imei_no}', "
                                f"Model={record.phone_model}, ID={record.id}, Used={record.used}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  Deleting: IMEI='{record.imei_no}', "
                                f"Model={record.phone_model}, ID={record.id}, Used={record.used}"
                            )
                        )
                        record.delete()
                        deleted_count += 1

                if non_vivo_records:
                    self.stdout.write(
                        self.style.NOTICE(
                            f"  Kept {len(non_vivo_records)} non-vivo record(s)"
                        )
                    )
            else:
                self.stdout.write(
                    self.style.NOTICE("  No vivo records found in this duplicate group")
                )

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
