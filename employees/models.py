# employees/models.py
import uuid
from django.utils import timezone
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models, transaction
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from Human_Resources.models import Role  
from branches.models import Branch  

# Phone validator (E.164-ish)
PHONE_REGEX = RegexValidator(regex=r'^\+?\d{7,15}$',
                             message="Phone must be in the format +233XXXXXXXXX or XXXXXXXXX.")

def generate_employee_id():
    # short uuid prefixed with EMP-
    return f"EMP-{uuid.uuid4().hex[:8].upper()}"


class EmployeeManager(BaseUserManager):
    def create_user(self, employee_email, password=None, **extra_fields):
        if not employee_email:
            raise ValueError("employee_email is required")
        email = self.normalize_email(employee_email)
        extra_fields.setdefault('is_active', True)
        user = self.model(employee_email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, employee_email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(employee_email, password, **extra_fields)


class Asset(models.Model):
    ASSET_TYPES = [
        ('LAPTOP', 'Laptop'),
        ('PHONE', 'Mobile Phone'),
        ('PRINTER', 'Printer'),
        ('GENERATOR', 'Generator'),
        ('OTHER', 'Other'),
    ]
    asset_tag = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=32, choices=ASSET_TYPES)
    serial_number = models.CharField(max_length=120, blank=True, null=True)
    assigned_to = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='assets')
    assigned_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.asset_tag} | {self.name}"


class SalaryHistory(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='salary_history')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('Employee', null=True, blank=True, on_delete=models.SET_NULL, related_name='salary_changes_made')

    class Meta:
        ordering = ['-effective_from']


class Certification(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255, blank=True, null=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    file = models.FileField(upload_to='certifications/', null=True, blank=True)


class EmergencyContact(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, validators=[PHONE_REGEX])
    alt_phone = models.CharField(max_length=15, validators=[PHONE_REGEX], blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    primary = models.BooleanField(default=False)  # allow multiple but one primary ideally


class Employee(AbstractBaseUser, PermissionsMixin):
    # PERSONAL
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255)
    preferred_name = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=32, blank=True, null=True)
    national_id_number = models.CharField(max_length=64, blank=True, null=True)  # GhanaCard
    phone_number = models.CharField(max_length=15, validators=[PHONE_REGEX], blank=True, null=True)
    personal_email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='employee_pics/', blank=True, null=True)

    # EMPLOYMENT
    employee_id = models.CharField(max_length=32, unique=True, blank=True, null=True, db_index=True)
    employee_email = models.EmailField(unique=True)
    position_title = models.CharField(max_length=255, blank=True, null=True)

    # department now a FK to Department (Human_Resources.Department)
    department = models.ForeignKey(
        'Human_Resources.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )

    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    primary_role = models.CharField(max_length=100, blank=True, null=True)   # quick primary role code
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    region = models.CharField(max_length=100, blank=True, null=True)

    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')

    EMP_TYPE_CHOICES = [
        ('PERMANENT', 'Permanent'),
        ('CONTRACTOR', 'Contractor'),
        ('TEMPORARY', 'Temporary'),
        ('INTERN', 'Intern'),
    ]
    employee_type = models.CharField(max_length=32, choices=EMP_TYPE_CHOICES, default='PERMANENT')

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('ON_LEAVE', 'On Leave'),
        ('SUSPENDED', 'Suspended'),
        ('TERMINATED', 'Terminated'),
    ]
    employment_status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='ACTIVE')

    hire_date = models.DateField(null=True, blank=True)
    contract_start = models.DateField(null=True, blank=True)
    contract_end = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)

    # PAYROLL / FINANCE (sensitive)
    current_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    pay_grade = models.CharField(max_length=100, blank=True, null=True)
    bank_account_number = models.CharField(max_length=64, blank=True, null=True)
    bank_name = models.CharField(max_length=120, blank=True, null=True)
    ssnit_number = models.CharField(max_length=64, blank=True, null=True)
    tin_number = models.CharField(max_length=64, blank=True, null=True)

    # WORK ARRANGEMENT
    work_schedule = models.CharField(max_length=100, blank=True, null=True)
    shift_preference = models.CharField(max_length=100, blank=True, null=True)
    onsite_required = models.BooleanField(default=True)
    remote_ok = models.BooleanField(default=False)

    # ASSETS: use Asset model (reverse FK 'assets')
    notes = models.TextField(blank=True, null=True)

    # TRAINING / EDUCATION
    education_level = models.CharField(max_length=64, blank=True, null=True)
    # certifications relation exists (Certification model)

    # AUTH & ADMIN
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)  # soft delete

    # integration fields
    external_auth_id = models.CharField(max_length=255, blank=True, null=True)  # for SSO / external providers
    external_payroll_id = models.CharField(max_length=255, blank=True, null=True)

    objects = EmployeeManager()

    USERNAME_FIELD = "employee_email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_email})"

    def soft_delete(self, by_user=None):
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['deleted_at', 'is_active'])
        # optionally log who deleted

    def restore(self):
        self.deleted_at = None
        self.is_active = True
        self.save(update_fields=['deleted_at', 'is_active'])

    def save(self, *args, **kwargs):
        # ensure employee_id set once, race-safe in transaction when creating
        if not self.employee_id:
            # attempt to create a stable unique id
            for _ in range(5):
                candidate = generate_employee_id()
                if not Employee.objects.filter(employee_id=candidate).exists():
                    self.employee_id = candidate
                    break
            if not self.employee_id:
                # fallback to uuid hex
                self.employee_id = f"EMP-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
