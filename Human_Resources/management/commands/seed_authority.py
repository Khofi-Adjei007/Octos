from django.core.management.base import BaseCommand
from django.db import transaction

from Human_Resources.models.authority import AuthorityRole


class Command(BaseCommand):
    help = "Seed canonical authority roles (scoped RBAC)"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("\n=== Seeding Authority Roles ===")

        roles = {
            "SUPER_ADMIN": {
                "name": "Super Administrator",
                "description": "Global system owner with full control",
                "allowed_scopes": [AuthorityRole.SCOPE_GLOBAL],
            },
            "HR_ADMIN": {
                "name": "HR Administrator",
                "description": "Regional HR operator",
                "allowed_scopes": [AuthorityRole.SCOPE_REGION],
            },
            "BELT_HR_OVERSEER": {
                "name": "Belt HR Overseer",
                "description": "Belt-level HR oversight and escalation",
                "allowed_scopes": [AuthorityRole.SCOPE_BELT],
            },
            "BRANCH_MANAGER": {
                "name": "Branch Manager",
                "description": "Branch-level operational manager",
                "allowed_scopes": [AuthorityRole.SCOPE_BRANCH],
            },
            "STAFF": {
                "name": "Staff",
                "description": "Standard employee with self-scoped access",
                "allowed_scopes": [AuthorityRole.SCOPE_BRANCH],
            },
        }

        for code, data in roles.items():
            role, created = AuthorityRole.objects.get_or_create(
                code=code,
                defaults={
                    "name": data["name"],
                    "description": data["description"],
                    "allowed_scopes": data["allowed_scopes"],
                },
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"✔ Created authority role: {code}")
                )
            else:
                self.stdout.write(f"• Authority role exists: {code}")

        self.stdout.write(
            self.style.SUCCESS("\nAuthority role seeding completed.\n")
        )
