from django.core.management.base import BaseCommand
from django.db import transaction

from Human_Resources.models.authority import AuthorityRole
from Human_Resources.models.permission import Permission


class Command(BaseCommand):
    help = "Seed AuthorityRole ↔ Permission mappings"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("\n=== Seeding Authority Role Permissions ===")

        # -------------------------------------------------
        # Permission mappings (explicit, canonical)
        # -------------------------------------------------

        role_permissions = {
            "HR_ADMIN": [
                "employee.view",
                "employee.create",
                "employee.update",
                "employee.deactivate",
                "recruitment.view",
                "recruitment.review",
                "recruitment.approve",
                "salary.view",
                "salary.edit",
            ],
            "BELT_HR_OVERSEER": [
                "employee.view",
                "branch.view",
                "recruitment.view",
                "salary.view",
            ],
            "BRANCH_MANAGER": [
                "employee.view",
                "branch.view",
                "branch.manage",
            ],
            "STAFF": [
                "employee.view",
            ],
        }

        # SUPER_ADMIN handled separately (gets everything)

        # -------------------------------------------------
        # Apply mappings
        # -------------------------------------------------

        for role_code, permission_codes in role_permissions.items():
            role = AuthorityRole.objects.get(code=role_code)

            permissions = list(
                Permission.objects.filter(code__in=permission_codes)
            )

            role.permissions.set(permissions)

            self.stdout.write(
                self.style.SUCCESS(
                    f"✔ {role_code}: {len(permissions)} permissions assigned"
                )
            )

        # -------------------------------------------------
        # SUPER_ADMIN gets ALL permissions
        # -------------------------------------------------

        super_admin = AuthorityRole.objects.get(code="SUPER_ADMIN")
        all_permissions = Permission.objects.all()
        super_admin.permissions.set(all_permissions)

        self.stdout.write(
            self.style.SUCCESS(
                f"✔ SUPER_ADMIN: {all_permissions.count()} permissions assigned (ALL)"
            )
        )

        self.stdout.write(
            self.style.SUCCESS("\nAuthority permission seeding completed.\n")
        )
