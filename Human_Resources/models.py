# Human_Resources/models.py

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

import uuid
from datetime import timedelta


# ============================================================
# Helpers & Validators
# ============================================================

def validate_resume_file(value):
    """
    Validate uploaded resume files.
    Allowed formats: PDF, DOC, DOCX
    Max size: 10MB
    """
    name = value.name.lower()
    allowed_extensions = ('.pdf', '.doc', '.docx')

    if not name.endswith(allowed_extensions):
        raise ValidationError('Only PDF, DOC, DOCX files are allowed.')

    if value.size > 10 * 1024 * 1024:
        raise ValidationError('File size must be less than 10MB.')


# ============================================================
# Core Reference Models
# ============================================================

class Department(models.Model):
    """
    Canonical department reference used across HR, Employees, and Branches.
    """
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Role(models.Model):
    """
    Job role / position.
    Used for permission mapping and organizational structure.
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=40, unique=True)  # e.g. BRANCH_MGR
    description = models.TextField(blank=True, null=True)
    default_pay_grade = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# ============================================================
# Authorization Models
# ============================================================

class Permission(models.Model):
    """
    Atomic system permission.
    Example: record_job, outsource_job, view_reports
    """
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    """
    Mapping between Role and Permission.
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="permission_roles")
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("role", "permission")
        ordering = ["role__name"]

    def __str__(self):
        return f"{self.role.code} → {self.permission.code}"


# ============================================================
# User Profile (Optional HR Extension)
# ============================================================

class UserProfile(models.Model):
    """
    Lightweight HR extension for authenticated users.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="userprofile"
    )
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    managed_branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Profile for {self.user}"


# ============================================================
# Recommendation / Onboarding Models
# ============================================================

class Recommendation(models.Model):
    """
    Internal referral / recommendation workflow.
    """

    ROLE_CHOICES = (
        ('branch_manager', 'Branch Manager'),
        ('regional_hr_manager', 'Regional HR Manager'),
        ('general_attendant', 'General Attendant'),
        ('cashier', 'Cashier'),
        ('graphic_designer', 'Graphic Designer'),
        ('large_format_machine_operator', 'Large Format/Machine Operator'),
        ('dispatch_rider', 'Dispatch Rider'),
        ('field_officer', 'Field Officer'),
        ('cleaner', 'Cleaner'),
        ('secretary', 'Secretary'),
        ('marketer', 'Marketer'),
        ('accountant', 'Accountant'),
        ('it_support', 'IT Support'),
        ('inventory_manager', 'Inventory Manager'),
        ('quality_control', 'Quality Control'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('interviewed', 'Interviewed'),
        ('offer_sent', 'Offer Sent'),
        ('onboarded', 'Onboarded'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )

    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50)

    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)

    recommended_role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    branch = models.ForeignKey("branches.Branch", on_delete=models.SET_NULL, null=True, blank=True)

    notes = models.TextField(blank=True)
    resume = models.FileField(
        upload_to="recommendation_resumes/",
        validators=[validate_resume_file],
        null=True,
        blank=True
    )

    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="pending")

    token = models.CharField(max_length=100, unique=True, blank=True, null=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    token_used = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations_made"
    )

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendation_case"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ONBOARDING_TOKEN_TTL_DAYS = 7

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid.uuid4())
            self.token_expires_at = timezone.now() + timedelta(days=self.ONBOARDING_TOKEN_TTL_DAYS)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.status})"


# ============================================================
# Public Application (External Applicants)
# ============================================================

class PublicApplication(models.Model):
    """
    External job application submitted via public-facing forms.
    """

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("under_review", "Under Review"),
        ("shortlisted", "Shortlisted"),
        ("rejected", "Rejected"),
        ("withdrawn", "Withdrawn"),
        ("hired", "Hired"),
    )

    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)

    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)

    recommended_role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="public_applications",
    )

    resume = models.FileField(
        upload_to="public_applications/resumes/",
        validators=[validate_resume_file],
        null=True,
        blank=True,
    )

    notes = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="public_applications_created",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.status})"


# ============================================================
# Audit & Operational Models
# ============================================================

class AuditLog(models.Model):
    """
    Immutable audit trail for HR and onboarding events.
    """
    action = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} @ {self.timestamp}"

# ============================================================
#Human resource Authority Models
# ============================================================
class Belt(models.Model):
    """
    Geopolitical authority layer.
    Immutable classification used for HR scoping.
    """

    code = models.CharField(
        max_length=16,
        unique=True,
        help_text="Short immutable code e.g. SOUTH, MID, NORTH",
    )

    name = models.CharField(
        max_length=100,
        help_text="Human-readable belt name",
    )

    order = models.PositiveSmallIntegerField(
        help_text="Ordering from south to north",
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name

class HRResponsibility(models.Model):
    """
    Defines a specific HR capability.
    Examples: Recruitment, Payroll Preparation, Compliance.
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Machine-readable code e.g. PAYROLL_PREP",
    )

    name = models.CharField(
        max_length=100,
        help_text="Human-readable responsibility name",
    )

    description = models.TextField(
        blank=True,
        help_text="Optional description of responsibility",
    )

    def __str__(self):
        return self.name


class HRScope(models.Model):
    """
    Defines an HR authority boundary.
    Scope is either belt-level OR region-level.
    """

    name = models.CharField(
        max_length=150,
        help_text="Descriptive scope name",
    )

    belt = models.ForeignKey(
        "Belt",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="hr_scopes",
        help_text="Belt-level scope (mutually exclusive with region)",
    )

    region = models.ForeignKey(
        "branches.Region",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="hr_scopes",
        help_text="Region-level scope (mutually exclusive with belt)",
    )

    responsibilities = models.ManyToManyField(
        HRResponsibility,
        related_name="scopes",
        help_text="Responsibilities granted within this scope",
    )

    visibility_level = models.CharField(
        max_length=20,
        choices=[
            ("LOCAL", "Local"),
            ("BELT", "Belt"),
            ("GLOBAL", "Global"),
        ],
        default="LOCAL",
        help_text="Defines visibility breadth without implying authority",
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(belt__isnull=False, region__isnull=True)
                    | models.Q(belt__isnull=True, region__isnull=False)
                ),
                name="hrscope_requires_exactly_one_geography",
            )
        ]

    def __str__(self):
        return self.name


class HRScopeAssignment(models.Model):
    """
    Assigns an HR scope to an employee.
    This is the actual authority grant.
    """

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="hr_scope_assignments",
    )

    scope = models.ForeignKey(
        HRScope,
        on_delete=models.CASCADE,
        related_name="assignments",
    )

    is_primary = models.BooleanField(
        default=False,
        help_text="Marks the employee's primary HR scope",
    )

    start_date = models.DateField(
        help_text="When this assignment becomes active",
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Optional end date for temporary or acting assignments",
    )

    assigned_by = models.ForeignKey(
        "employees.Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hr_scope_assignments_given",
    )

    class Meta:
        unique_together = ("employee", "scope", "start_date")

    def __str__(self):
        return f"{self.employee} → {self.scope}"


