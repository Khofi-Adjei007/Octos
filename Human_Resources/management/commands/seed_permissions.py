# Human_Resources/management/commands/seed_permissions.py

from django.core.management.base import BaseCommand
from Human_Resources.models import Permission


PERMISSIONS = [
    # Jobs
    ("record_job", "Record Job", "Create quick / walk-in jobs"),
    ("edit_job", "Edit Job", "Modify existing jobs"),
    ("cancel_job", "Cancel Job", "Cancel queued or active jobs"),
    ("outsource_job", "Outsource Job", "Outsource jobs to vendors"),

    # Visibility
    ("view_reports", "View Reports", "View operational and performance reports"),
    ("view_finance", "View Finance", "Access financial data"),

    # Administration
    ("manage_employees", "Manage Employees", "HR employee management"),
    ("manage_branch", "Manage Branch", "Branch configuration and setup"),
]


class Command(BaseCommand):
    help = "Seed system permissions (safe to run multiple times)"

    def handle(self, *args, **options):
        created_count = 0

        for code, name, description in PERMISSIONS:
            _, created = Permission.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": description,
                },
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Permission seeding complete. New permissions created: {created_count}"
            )
        )
