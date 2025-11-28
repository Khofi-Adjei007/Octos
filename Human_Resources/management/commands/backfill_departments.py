# Human_Resources/management/commands/backfill_departments.py
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from Human_Resources.models import Department
from employees.models import Employee
from django.db import transaction

class Command(BaseCommand):
    help = "Backfill Department model from Employee.department (text) into department_new FK"

    def handle(self, *args, **options):
        with transaction.atomic():
            names = Employee.objects.values_list('department', flat=True).distinct()
            for name in names:
                if not name:
                    self.stdout.write("Skipping empty/NULL department")
                    continue
                # create a safe unique code
                code = slugify(name)[:50] or name[:50]
                dept, created = Department.objects.get_or_create(code=code, defaults={'name': name})
                updated = Employee.objects.filter(department=name).update(department_new=dept)
                self.stdout.write(f"Mapped {name!r} -> Department(id={dept.id}, code='{dept.code}') (updated {updated} rows)")
            self.stdout.write(self.style.SUCCESS("Backfill complete."))
