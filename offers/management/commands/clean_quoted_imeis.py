from django.core.management.base import BaseCommand
from offers.models import IMEINO

class Command(BaseCommand):
    help = 'Clean up IMEI numbers that contain duplicate quoted values, removing the quotes or deleting the duplicates.'

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be cleaned/deleted without actually modifying the database",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if dry_run:
            self.stdout.write(self.style.WARNING("--- DRY RUN MODE: No database changes will be saved ---"))

        # Find all IMEINO records where imei_no starts and ends with double quotes (or single quotes)
        # We can also do a broad search or iterate over all of them.
        all_records = IMEINO.objects.all()
        
        quoted_records = []
        for record in all_records:
            val = record.imei_no.strip()
            # Check if it has surrounding quotes
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                quoted_records.append(record)

        self.stdout.write(self.style.NOTICE(f"Found {len(quoted_records)} records with quoted IMEI numbers."))

        deleted_count = 0
        updated_count = 0

        for record in quoted_records:
            original_imei = record.imei_no
            # Strip outer quotes
            clean_imei = original_imei.strip('"').strip("'")
            
            # Check if the clean IMEI already exists in the database
            exists = IMEINO.objects.filter(imei_no=clean_imei).exclude(id=record.id).exists()

            if exists:
                # If clean version already exists, we delete the quoted duplicate record
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[DRY RUN] Would DELETE quoted duplicate record ID {record.id}: '{original_imei}' (clean version '{clean_imei}' already exists)"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.DANGER(
                            f"DELETING quoted duplicate record ID {record.id}: '{original_imei}'"
                        )
                    )
                    record.delete()
                deleted_count += 1
            else:
                # If clean version doesn't exist, we remove the quotes and save the clean version
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[DRY RUN] Would UPDATE record ID {record.id}: '{original_imei}' -> '{clean_imei}'"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"UPDATING record ID {record.id}: '{original_imei}' -> '{clean_imei}'"
                        )
                    )
                    record.imei_no = clean_imei
                    record.save()
                updated_count += 1

        self.stdout.write("\nSummary:")
        self.stdout.write(self.style.SUCCESS(f"Total processed: {len(quoted_records)}"))
        self.stdout.write(self.style.SUCCESS(f"Deleted (duplicates): {deleted_count}"))
        self.stdout.write(self.style.SUCCESS(f"Updated (quotes removed): {updated_count}"))
