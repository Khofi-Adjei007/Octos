# Human_Resources/management/commands/seed_authority_permissions.py

from django.core.management.base import BaseCommand
from django.db import transaction

from Human_Resources.models.authority import AuthorityRole
from Human_Resources.models.permission import Permission


class Command(BaseCommand):
    help = "Seed AuthorityRole ↔ Permission mappings"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("\n=== Seeding Authority Role Permissions ===")

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
                "VIEW_RECRUITMENT",
                "ADVANCE_APPLICATION",
                "HIRE_CANDIDATE",
                "RECOMMEND_CANDIDATE",
                "MANAGE_RECRUITMENT",
                "manage_employees",
                "view_reports",
            ],
            "BELT_HR_OVERSEER": [
                "employee.view",
                "branch.view",
                "recruitment.view",
                "salary.view",
                "VIEW_RECRUITMENT",
                "ADVANCE_APPLICATION",
                "view_reports",
            ],
            "BRANCH_MANAGER": [
                "employee.view",
                "branch.view",
                "branch.manage",
                "VIEW_RECRUITMENT",
                "RECOMMEND_CANDIDATE",
                "view_reports",
                "manage_branch",
            ],
            "STAFF": [
                "employee.view",
            ],
        }

        for role_code, permission_codes in role_permissions.items():
            try:
                role = AuthorityRole.objects.get(code=role_code)
            except AuthorityRole.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"✘ AuthorityRole not found, skipped: {role_code}")
                )
                continue

            permissions = list(
                Permission.objects.filter(code__in=permission_codes)
            )

            role.permissions.set(permissions)

            self.stdout.write(
                self.style.SUCCESS(
                    f"✔ {role_code}: {len(permissions)} permissions assigned"
                )
            )

        # SUPER_ADMIN gets everything
        try:
            super_admin = AuthorityRole.objects.get(code="SUPER_ADMIN")
            all_permissions = Permission.objects.all()
            super_admin.permissions.set(all_permissions)
            self.stdout.write(
                self.style.SUCCESS(
                    f"✔ SUPER_ADMIN: {all_permissions.count()} permissions assigned (ALL)"
                )
            )
        except AuthorityRole.DoesNotExist:
            self.stdout.write(
                self.style.WARNING("✘ SUPER_ADMIN role not found, skipped.")
            )

        self.stdout.write(
            self.style.SUCCESS("\nAuthority permission seeding completed.\n")
        )