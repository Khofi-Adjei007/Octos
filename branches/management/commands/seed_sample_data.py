# branches/management/commands/seed_sample_data.py
from django.core.management.base import BaseCommand
from importlib import import_module
from django.db import transaction, IntegrityError, DatabaseError
from django.utils import timezone
from Human_Resources.models import Role
from employees.models import Employee
import random, sys, traceback

# Import models dynamically
mods = import_module('branches.models')
Branch = mods.Branch
# Some projects name these differently; try common names
Country = getattr(mods, 'Country', None)
Region  = getattr(mods, 'Region', None)

class Command(BaseCommand):
    help = "Seed branch + minimal Country/Region (if needed) + sample employees."

    def _create_country_if_missing(self, desired_name='Ghana'):
        if Country is None:
            return None
        obj, created = Country.objects.get_or_create(name=desired_name)
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Country: {obj}"))
        return obj

    def _create_region_if_missing(self, region_name='Greater Accra', country_obj=None):
        if Region is None:
            return None
        defaults = {}
        # if Region has a country FK field named 'country', pass it; otherwise adapt
        if country_obj is not None:
            # find which fk field on Region points to Country
            for f in Region._meta.fields:
                if getattr(f, 'remote_field', None) and getattr(f.remote_field, 'model', None) == Country:
                    defaults[f.name] = country_obj
                    break
        region, created = Region.objects.get_or_create(name=region_name, defaults=defaults)
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Region: {region}"))
        return region

    def _determine_lookup_field(self):
        # prefer 'name' for Branch lookups; otherwise first non-pk CharField
        if 'name' in [f.name for f in Branch._meta.fields]:
            return 'name'
        for f in Branch._meta.fields:
            if f.get_internal_type() in ('CharField','TextField') and not getattr(f,'primary_key',False):
                return f.name
        return None

    def handle(self, *args, **options):
        # create required related rows first
        country = self._create_country_if_missing('Ghana')
        region = self._create_region_if_missing('Greater Accra', country_obj=country)

        # build branch lookup/create kwargs
        branch_lookup_field = self._determine_lookup_field()
        branch_name = "Head Station - Accra"
        create_defaults = {}

        # populate sensible fields if present
        for f in Branch._meta.fields:
            if f.name in ('code','phone','email','is_main','is_active'):
                # give a default only for fields that exist
                if f.get_internal_type() == 'BooleanField':
                    create_defaults[f.name] = True if f.name=='is_main' else True
                elif f.get_internal_type().startswith('Char') or f.get_internal_type()=='EmailField':
                    create_defaults[f.name] = f"sample-{f.name}"
            # if Branch has FK fields 'region' or 'country' set them explicitly
            if getattr(f,'remote_field',None):
                rel_model = f.remote_field.model
                if rel_model == Region and region is not None:
                    create_defaults[f.name] = region
                if rel_model == Country and country is not None:
                    create_defaults[f.name] = country

        if branch_lookup_field:
            lookup = {branch_lookup_field: branch_name}
            create_defaults[branch_lookup_field] = branch_name
        else:
            lookup = {'id': 1}
            create_defaults['name'] = branch_name

        try:
            with transaction.atomic():
                branch, created = Branch.objects.get_or_create(**lookup, defaults=create_defaults)
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created Branch: {branch}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Branch exists: {branch}"))
        except (IntegrityError, DatabaseError) as e:
            self.stdout.write(self.style.ERROR("DB error creating Branch: " + str(e)))
            traceback.print_exc(file=sys.stdout)
            return

        # create sample employees (non-fatal if one fails)
        def make_employee(email, first, last, role_code, is_staff=False, branch_obj=branch):
            try:
                if Employee.objects.filter(employee_email=email).exists():
                    self.stdout.write(self.style.NOTICE(f"Employee exists: {email}"))
                    return
                role = Role.objects.filter(code=role_code).first()
                emp = Employee(
                    first_name=first,
                    last_name=last,
                    employee_email=email,
                    phone_number=f"+23320{random.randint(1000000,9999999)}",
                    position_title=(role.name if role else role_code),
                    role=role,
                    branch=branch_obj,
                    is_staff=is_staff,
                    is_active=True
                )
                emp.set_password("P@ssw0rd123")
                emp.save()
                self.stdout.write(self.style.SUCCESS(f"Created employee {email}"))
            except Exception as ex:
                self.stdout.write(self.style.ERROR(f"Failed creating employee {email}: {ex}"))

        make_employee("ceo@farhat.local","CEO","Farhat","CEO",is_staff=True,branch_obj=None)
        make_employee("mgr.accra@farhat.local","Ama","Owusu","BRANCH_MGR",is_staff=True,branch_obj=branch)
        make_employee("design1@farhat.local","Kojo","Mensah","DESIGNER",is_staff=False,branch_obj=branch)
        make_employee("cash.accra@farhat.local","Efua","Amoah","CASHIER",is_staff=False,branch_obj=branch)

        self.stdout.write(self.style.SUCCESS("Seeding complete. Default password: P@ssw0rd123"))
