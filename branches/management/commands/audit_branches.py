from django.core.management.base import BaseCommand
from branches.models import Branch


class Command(BaseCommand):
    help = "Audit branch → region → belt consistency (read-only)"

    def handle(self, *args, **options):
        self.stdout.write("\n=== Branch → Region Audit ===\n")

        issues = {
            "missing_region": [],
            "country_mismatch": [],
            "city_region_mismatch": [],
            "district_region_mismatch": [],
        }

        branches = (
            Branch.objects
            .select_related(
                "country",
                "region",
                "region__belt",
                "city",
                "city__region",
                "district",
                "district__city__region",
            )
            .order_by("name")
        )

        for branch in branches:
            header = f"{branch.name} ({branch.code})"

            # -------------------------------------------------
            # 1. Missing region
            # -------------------------------------------------
            if not branch.region:
                issues["missing_region"].append(branch)
                self.stdout.write(
                    self.style.ERROR(f"✖ {header} — NO REGION ASSIGNED")
                )
                continue

            region = branch.region
            belt = region.belt.code if region.belt else "❌ NO BELT"

            self.stdout.write(
                f"• {header} → {region.name} [{belt}]"
            )

            # -------------------------------------------------
            # 2. Country consistency
            # -------------------------------------------------
            if branch.country_id != region.country_id:
                issues["country_mismatch"].append(branch)
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ Country mismatch: "
                        f"Branch={branch.country.code}, "
                        f"Region={region.country.code}"
                    )
                )

            # -------------------------------------------------
            # 3. City → Region consistency
            # -------------------------------------------------
            if branch.city:
                if branch.city.region_id != region.id:
                    issues["city_region_mismatch"].append(branch)
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ City mismatch: "
                            f"{branch.city.name} belongs to "
                            f"{branch.city.region.name}, "
                            f"but branch region is {region.name}"
                        )
                    )

            # -------------------------------------------------
            # 4. District → City → Region consistency
            # -------------------------------------------------
            if branch.district:
                district_region = branch.district.city.region
                if district_region.id != region.id:
                    issues["district_region_mismatch"].append(branch)
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ District mismatch: "
                            f"{branch.district.name} → "
                            f"{district_region.name}, "
                            f"but branch region is {region.name}"
                        )
                    )

        # -------------------------------------------------
        # FINAL SUMMARY
        # -------------------------------------------------

        self.stdout.write("\n=== Audit Summary ===")

        if not any(issues.values()):
            self.stdout.write(
                self.style.SUCCESS(
                    "✔ All branches are correctly mapped to regions and belts."
                )
            )
            return

        for key, items in issues.items():
            if items:
                self.stdout.write(
                    self.style.ERROR(
                        f"{key.replace('_', ' ').title()}: {len(items)} issue(s)"
                    )
                )

        self.stdout.write(
            "\nNo data was modified. Review issues and fix deliberately.\n"
        )
                    