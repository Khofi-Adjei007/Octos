from django.core.management.base import BaseCommand
from django.db import transaction

from Human_Resources.models import Belt
from branches.models import Region


class Command(BaseCommand):
    help = "Seed canonical HR base data: Belts and Regions (safe, idempotent, non-destructive)"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("\n=== Seeding HR Canonical Data ==="))

        # Track non-blocking issues for final report
        mismatched_regions = []

        # -------------------------------------------------
        # 1. BELTS (GEOGRAPHIC / OPERATIONAL)
        # -------------------------------------------------
        # Canon:
        # - Codes are immutable
        # - Order is explicit and required
        # - Existing rows are never auto-mutated
        # -------------------------------------------------

        belts = {
            "SOUTH": {
                "name": "Southern Belt",
                "order": 10,
            },
            "MIDDLE": {
                "name": "Middle Belt",
                "order": 20,
            },
            "NORTH": {
                "name": "Northern Belt",
                "order": 30,
            },
        }

        belt_objs = {}

        for code, data in belts.items():
            belt, created = Belt.objects.get_or_create(
                code=code,
                defaults={
                    "name": data["name"],
                    "order": data["order"],
                },
            )

            belt_objs[code] = belt

            if created:
                self.stdout.write(self.style.SUCCESS(f"✔ Created Belt: {code}"))
            else:
                self.stdout.write(f"• Belt exists: {code}")

        # -------------------------------------------------
        # 2. REGIONS (GHANA – CANONICAL BELT MAPPING)
        # -------------------------------------------------
        # Rules:
        # - Regions are created if missing
        # - Existing regions are NEVER auto-moved
        # - Mismatches are reported, not fatal
        # -------------------------------------------------

        regions_by_belt = {
            "SOUTH": [
                "Greater Accra",
                "Central",
                "Western",
                "Volta",
            ],
            "MIDDLE": [
                "Western North",
                "Eastern",
                "Ashanti",
                "Bono",
                "Bono East",
                "Ahafo",
                "Oti",
            ],
            "NORTH": [
                "Northern",
                "North East",
                "Savannah",
                "Upper East",
                "Upper West",
            ],
        }

        for belt_code, region_names in regions_by_belt.items():
            belt = belt_objs[belt_code]

            for region_name in region_names:
                region, created = Region.objects.get_or_create(
                    name=region_name,
                    defaults={"belt": belt},
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✔ Created Region: {region_name} → {belt.code}"
                        )
                    )
                    continue

                # Existing region: verify belt assignment
                if region.belt_id != belt.id:
                    mismatched_regions.append(
                        {
                            "region": region_name,
                            "current": region.belt.code,
                            "expected": belt.code,
                        }
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            f"! Region mismatch: {region_name} "
                            f"(current={region.belt.code}, expected={belt.code})"
                        )
                    )
                else:
                    self.stdout.write(
                        f"• Region exists: {region_name} → {belt.code}"
                    )

        # -------------------------------------------------
        # 3. FINAL REPORT
        # -------------------------------------------------

        self.stdout.write("\n=== Seeding Summary ===")

        if mismatched_regions:
            self.stdout.write(
                self.style.ERROR(
                    f"{len(mismatched_regions)} region(s) have belt mismatches."
                )
            )
            self.stdout.write(
                "These were NOT auto-corrected. Review and fix deliberately:\n"
            )

            for item in mismatched_regions:
                self.stdout.write(
                    f" - {item['region']}: "
                    f"{item['current']} → {item['expected']}"
                )

            self.stdout.write(
                "\nOnce corrected, re-run `python manage.py seed_hr`."
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "All belts and regions are correctly aligned with canon."
                )
            )

        self.stdout.write(self.style.SUCCESS("\nHR base data seeding completed.\n"))
