from django.core.management.base import BaseCommand, CommandError

from offers.models import IMEINO, LuckyDrawSystem
from offers.services.imei_service import delete_imeis_for_lucky_draw_system


class Command(BaseCommand):
    help = (
        "Safely and efficiently bulk delete IMEI numbers for a selected Lucky Draw System. "
        "Optimized for large datasets (e.g. 40,000+ records) with chunked batching."
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
            "--batch-size",
            dest="batch_size",
            type=int,
            default=5000,
            help="Number of records to delete per batch (default: 5000). Set to 0 for a single atomic query.",
        )
        parser.add_argument(
            "--only-unused",
            dest="only_unused",
            action="store_true",
            help="Only delete IMEI numbers that have not been used (used=False). Default is to delete all.",
        )
        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="Simulate the deletion and output counts without deleting any records.",
        )
        parser.add_argument(
            "-y",
            "--yes",
            dest="confirm",
            action="store_true",
            help="Skip confirmation prompt and proceed immediately.",
        )

    def handle(self, *args, **options):
        system_id = options.get("system_id")
        name = options.get("name")
        batch_size = options.get("batch_size")
        only_unused = options.get("only_unused")
        dry_run = options.get("dry_run")
        confirm = options.get("confirm")

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

        # 2. Inspect record counts
        all_qs = IMEINO.objects.filter(lucky_draw_system=lucky_draw)
        total_count = all_qs.count()
        used_count = all_qs.filter(used=True).count()
        unused_count = total_count - used_count

        to_delete_count = unused_count if only_unused else total_count

        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(
            self.style.NOTICE(
                f"Lucky Draw System : {lucky_draw.name} (ID: {lucky_draw.id})"
            )
        )
        self.stdout.write(
            self.style.NOTICE(f"Organization      : {lucky_draw.organization}")
        )
        self.stdout.write(f"Total IMEIs       : {total_count}")
        self.stdout.write(f"Used IMEIs        : {used_count}")
        self.stdout.write(f"Unused IMEIs      : {unused_count}")
        self.stdout.write(
            self.style.WARNING(
                f"Mode              : {'ONLY UNUSED' if only_unused else 'ALL IMEIs'}"
            )
        )
        self.stdout.write(self.style.WARNING(f"Records to delete : {to_delete_count}"))
        self.stdout.write(
            f"Batch size        : {batch_size if batch_size > 0 else 'Single query'}"
        )
        self.stdout.write(self.style.NOTICE("=" * 60))

        if to_delete_count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "No IMEI records match the deletion criteria. Nothing to do."
                )
            )
            return

        # 3. Dry-run mode
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"[DRY RUN] Would delete {to_delete_count} IMEI numbers. No changes were made."
                )
            )
            return

        # 4. Confirmation prompt
        if not confirm:
            self.stdout.write(
                self.style.ERROR(
                    f"\nWARNING: You are about to permanently delete {to_delete_count} IMEI numbers for '{lucky_draw.name}'."
                )
            )
            response = input("Type 'yes' to confirm deletion: ")
            if response.strip().lower() != "yes":
                self.stdout.write(self.style.NOTICE("Operation cancelled by user."))
                return

        # 5. Progress callback
        def print_progress(deleted, total):
            pct = (deleted / total * 100) if total else 100
            self.stdout.write(
                f"  --> Deleted {deleted:,}/{total:,} IMEIs ({pct:.1f}%)..."
            )

        # 6. Execute via service
        self.stdout.write(self.style.NOTICE("\nStarting bulk deletion..."))
        result = delete_imeis_for_lucky_draw_system(
            lucky_draw_system_id=lucky_draw.id,
            only_unused=only_unused,
            batch_size=batch_size,
            progress_callback=print_progress,
        )

        self.stdout.write(self.style.SUCCESS(f"\n[SUCCESS] {result['message']}"))
