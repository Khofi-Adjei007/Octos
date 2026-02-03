from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
from datetime import timedelta
from Human_Resources.models.role import Role
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
# Recommendation / Onboarding Models
# ============================================================
# ⚠️ LEGACY MODEL
# Do not extend or add new logic.
# Pending migration to RecruitmentApplication.
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
# ⚠️ LEGACY MODEL
# Do not extend or add new logic.
# Pending migration to RecruitmentApplication.
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
