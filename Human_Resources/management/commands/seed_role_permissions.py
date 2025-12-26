# Human_Resources/management/commands/seed_role_permissions.py

from django.core.management.base import BaseCommand
from Human_Resources.models import Role, Permission, RolePermission


ROLE_PERMISSION_MAP = {
    # Front desk / walk-in handling
    "GENERAL_ATTENDANT": [
        "record_job",
    ],

    # Supervisor
    "SUPERVISOR": [
        "record_job",
        "edit_job",
        "cancel_job",
    ],

    # Branch Manager
    "BRANCH_MANAGER": [
        "record_job",
        "edit_job",
        "cancel_job",
        "outsource_job",
        "view_reports",
        "manage_branch",
    ],

    # HR
    "HR_MANAGER": [
        "manage_employees",
        "view_reports",
    ],

    # Finance
    "FINANCE_MANAGER": [
        "view_finance",
        "view_reports",
    ],
}


class Command(BaseCommand):
    help = "Seed role → permission mappings (safe to re-run)"

    def handle(self, *args, **options):
        assigned = 0
        skipped_roles = 0
        skipped_permissions = 0

        for role_code, permission_codes in ROLE_PERMISSION_MAP.items():
            try:
                role = Role.objects.get(code=role_code)
            except Role.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"Role not found, skipped: {role_code}")
                )
                skipped_roles += 1
                continue

            for perm_code in permission_codes:
                try:
                    permission = Permission.objects.get(code=perm_code)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Permission not found ({perm_code}) for role {role_code}"
                        )
                    )
                    skipped_permissions += 1
                    continue

                _, created = RolePermission.objects.get_or_create(
                    role=role,
                    permission=permission,
                )

                if created:
                    assigned += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Role-permission seeding complete. "
                f"Assigned: {assigned}, "
                f"Missing roles: {skipped_roles}, "
                f"Missing permissions: {skipped_permissions}"
            )
        )
