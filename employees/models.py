# employees/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db import models
from Human_Resources.models import Role

class EmployeeManager(BaseUserManager):
    def create_user(self, employee_email, password=None, **extra_fields):
        if not employee_email:
            raise ValueError("Employees must have an email address")
        email = self.normalize_email(employee_email)
        user = self.model(employee_email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, employee_email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(employee_email, password, **extra_fields)

class Employee(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=255, blank=False, null=False)
    middle_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=False, null=False)
    employee_email = models.EmailField(unique=True, blank=False)
    phone_number = models.CharField(max_length=15, blank=False, null=False)
    date_of_birth = models.DateField(blank=False, null=False)   
    address = models.TextField(blank=False, null=False)
    groups = models.ManyToManyField(Group, related_name="employee_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="employee_permissions", blank=True)

    # Work-related Information
    HR = 'HR'
    IT = 'IT'
    SALES = 'SALES'
    MARKETING = 'MARKETING'
    ACCOUNTING = 'ACCOUNTING'
    MANAGEMENT = 'MANAGEMENT'
    OPERATIONS = 'OPERATIONS'
    DELIVERY = 'DELIVERY'
    QUALITY_CONTROL = 'QUALITY_CONTROL'

    DEPARTMENTS = [
        (HR, 'Human Resources'),
        (IT, 'Information Technology'),
        (SALES, 'Sales'),
        (MARKETING, 'Marketing'),
        (ACCOUNTING, 'Accounting'),
        (MANAGEMENT, 'Management'),
        (OPERATIONS, 'Operations'),
        (DELIVERY, 'Delivery'),
        (QUALITY_CONTROL, 'Quality Control'),
    ]
    
    employee_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    position = models.CharField(max_length=255, null=True, blank=True)
    department = models.CharField(max_length=255, choices=DEPARTMENTS, null=True, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    requested_role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees_requesting')

    # Employment Status
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    work_schedule = models.CharField(max_length=50, null=True, blank=True)
    contract_type = models.CharField(max_length=50, choices=[('permanent', 'Permanent'), ('temporary', 'Temporary')])

    # Emergency Contact Information
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)

    # Education & Certifications
    PRIMARY = 'PRIMARY'
    JHS = 'JHS'
    SHS = 'SHS'
    UNDERGRADUATE = 'UNDERGRADUATE'
    POSTGRADUATE = 'POSTGRADUATE'
    DOCTORATE = 'DOCTORATE'
    VOCATIONAL = 'VOCATIONAL'
    OTHER = 'OTHER'

    EDUCATION_LEVELS = [
        (PRIMARY, 'Primary'),
        (JHS, 'Junior High School'),
        (SHS, 'Senior High School'),
        (UNDERGRADUATE, 'Undergraduate'),
        (POSTGRADUATE, 'Postgraduate'),
        (DOCTORATE, 'Doctorate'),
        (VOCATIONAL, 'Vocational Training'),
        (OTHER, 'Other'),
    ]

    education_level = models.CharField(max_length=255, blank=True, choices=EDUCATION_LEVELS, null=True)
    certifications = models.TextField(blank=True, null=True)

    # Role-Specific Information
    skills = models.TextField(blank=True, null=True)
    shift_preference = models.CharField(max_length=50, blank=True, null=True)

    EQUIPMENT_CHOICES = [
        ('LAPTOP', 'Laptop'),
        ('PHONE', 'Mobile Phone'),
        ('PRINTER', 'Printer'),
        ('HEADSET', 'Headset'),
        ('OTHER', 'Other'),
    ]

    equipment_assigned = models.CharField(
        max_length=50,
        choices=EQUIPMENT_CHOICES,
        blank=True,
        null=True,
        help_text="Select assigned equipment or choose 'Other' to specify."
    )
    equipment_other = models.TextField(blank=True, null=True, help_text="Specify equipment if not listed.")

    # Other Details
    profile_picture = models.ImageField(upload_to='employee_pics/', blank=True, null=True)
    date_of_last_performance_review = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    branch = models.ForeignKey(
        'branches.Branch',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='employees'
    )

    # Authentication Fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = EmployeeManager()

    USERNAME_FIELD = "employee_email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_email})"