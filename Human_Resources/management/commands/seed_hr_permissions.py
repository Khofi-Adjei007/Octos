from django.core.management.base import BaseCommand
from django.db import transaction

from Human_Resources.models.permission import Permission


class Command(BaseCommand):
    help = "Seed canonical HR permissions (authority & workflow layer)"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("\n=== Seeding Canonical HR Permissions ===")

        permissions = {
            # -------------------------------------------------
            # Employee
            # -------------------------------------------------
            "employee.view": "View employee records",
            "employee.create": "Create new employees",
            "employee.update": "Update employee records",
            "employee.deactivate": "Deactivate or terminate employees",

            # -------------------------------------------------
            # Recruitment
            # -------------------------------------------------
            "recruitment.view": "View recruitment applications",
            "recruitment.review": "Review recruitment applications",
            "recruitment.approve": "Approve recruitment applications",

            # -------------------------------------------------
            # Salary / Payroll
            # -------------------------------------------------
            "salary.view": "View salary and payroll data",
            "salary.edit": "Edit salary and payroll data",

            # -------------------------------------------------
            # Branch (HR-facing)
            # -------------------------------------------------
            "branch.view": "View branch information",
            "branch.manage": "Manage branch operations (HR scope)",
        }

        created = 0

        for code, description in permissions.items():
            _, was_created = Permission.objects.get_or_create(
                code=code,
                defaults={
                    "name": code.replace(".", " ").title(),
                    "description": description,
                },
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"✔ Created: {code}"))
            else:
                self.stdout.write(f"• Exists: {code}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nHR permission seeding complete ({created} created).\n"
            )
        )
