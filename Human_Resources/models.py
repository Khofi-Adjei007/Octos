# Human_Resources/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
from datetime import timedelta

# Validator for resume files (allow pdf/doc/docx). 10MB limit.
def validate_resume_file(value):
    name = value.name.lower()
    allowed = ('.pdf', '.doc', '.docx')
    if not any(name.endswith(ext) for ext in allowed):
        raise ValidationError('Only PDF, DOC, DOCX files are allowed.')
    if value.size > 10 * 1024 * 1024:  # 10MB limit
        raise ValidationError('File size must be less than 10MB.')

################################################
# Department & Role / JobProfile
################################################
class Department(models.Model):
    """Optional metadata for departments so branches and employees can reference structured data."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Role(models.Model):
    """
    Role / JobProfile used by Employee.role FK.
    Keep it lightweight but include a stable code for mapping to permissions or external systems.
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=40, unique=True)  # e.g., 'BRANCH_MGR', 'DESIGNER'
    description = models.TextField(blank=True, null=True)
    default_pay_grade = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

################################################
# Department Model
class Department(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return self.name



################################################
# UserProfile (optional, small wrapper)
################################################
class UserProfile(models.Model):
    """
    Lightweight profile linked to auth user for HR-specific quick fields.
    Note: many Employee fields exist on the custom user model already; this is for any extra per-user HR metadata.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='userprofile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    managed_branch = models.ForeignKey('branches.Branch', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Profile for {self.user}"


################################################
# Recommendation (referral / candidate record)
################################################
class Recommendation(models.Model):
    ROLE_CHOICES = (
        ('branch_manager', 'Branch Manager'),
        ('regional_hr_manager', 'Regional Human Resource Manager'),
        ('general_attendant', 'General Attendant'),
        ('cashier', 'Cashier'),
        ('graphic_designer', 'Graphic Designer'),
        ('large_format_machine_operator', 'Large Format/Machine Operator'),
        ('zonal_delivery_dispatch_rider', 'Zonal Delivery/Dispatch Rider'),
        ('field_officer', 'Field Officer'),
        ('cleaner', 'Cleaner'),
        ('secretary', 'Secretary'),
        ('marketer', 'Marketer'),
        ('accountant', 'Accountant'),
        ('it_support_technician', 'IT Support/Technician'),
        ('inventory_manager', 'Inventory Manager'),
        ('quality_control_inspector', 'Quality Control Inspector'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interviewed', 'Interviewed'),
        ('offer_sent', 'Offer Sent'),
        ('onboarded', 'Onboarded'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('rejected_by_candidate', 'Rejected by Candidate'),
        ('cancelled', 'Cancelled'),
    )

    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    recommended_role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    # Branch may be null in DB; business logic/forms should require it for branch-originated recommendations.
    branch = models.ForeignKey('branches.Branch', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    resume = models.FileField(upload_to='recommendation_resumes/', validators=[validate_resume_file], null=True, blank=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='pending')

    # single-use onboarding token
    token = models.CharField(max_length=100, unique=True, blank=True, null=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    token_used = models.BooleanField(default=False)

    # onboarding lifecycle fields
    onboarding_sent_at = models.DateTimeField(null=True, blank=True)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    onboarding_attempts = models.PositiveIntegerField(default=0)

    # link to Employee once created
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='recommendation_case')

    # who created the recommendation (branch manager / user). nullable to allow external submissions
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='recommendations_made')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # TTL in days for token; adjustable here if needed
    ONBOARDING_TOKEN_TTL_DAYS = 7

    def _ensure_token(self):
        if not self.token:
            self.token = str(uuid.uuid4())
        if not self.token_expires_at:
            self.token_expires_at = timezone.now() + timedelta(days=self.ONBOARDING_TOKEN_TTL_DAYS)

    def send_onboarding_link(self, send_func):
        """
        send_func should accept the Recommendation instance and perform the send (email/whatsapp).
        This updates onboarding_sent_at and increments attempts.
        """
        self._ensure_token()
        self.onboarding_sent_at = timezone.now()
        self.onboarding_attempts = (self.onboarding_attempts or 0) + 1
        self.token_used = False
        self.save(update_fields=['token', 'token_expires_at', 'onboarding_sent_at', 'onboarding_attempts', 'token_used'])
        send_func(self)

    def mark_token_used(self):
        self.token_used = True
        self.token_expires_at = timezone.now()
        self.onboarding_completed_at = timezone.now()
        self.status = 'onboarded'
        self.save(update_fields=['token_used', 'token_expires_at', 'onboarding_completed_at', 'status'])

    def token_is_valid(self):
        if not self.token or self.token_used:
            return False
        if self.token_expires_at and timezone.now() > self.token_expires_at:
            return False
        return True

    def clean(self):
        # business-level validation: if created_by exists and is a branch manager, branch should be set
        if self.created_by and not self.branch:
            # Don't block external recommendations that may be region-level. Raise ValidationError in form if desired.
            # For now, just allow but warn in logs (you can enforce in form/view)
            pass
        super().clean()

    def save(self, *args, **kwargs):
        # ensure token and expiry on create if not provided
        if not self.token:
            self.token = str(uuid.uuid4())
        if not self.token_expires_at:
            self.token_expires_at = timezone.now() + timedelta(days=self.ONBOARDING_TOKEN_TTL_DAYS)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Recommendation for {self.first_name} {self.last_name} - {self.status}"


################################################
# AuditLog Model (expanded)
################################################
class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('recommendation_created', 'Recommendation Created'),
        ('recommendation_approved', 'Recommendation Approved'),
        ('recommendation_rejected', 'Recommendation Rejected'),
        ('form_submitted', 'Form Submitted'),
        ('application_approved', 'Application Approved'),
        ('first_login', 'First Login'),
        ('password_reset', 'Password Reset'),
        ('onboarding_link_sent', 'Onboarding Link Sent'),
        ('onboarding_link_resent', 'Onboarding Link Resent'),
        ('onboarding_completed', 'Onboarding Completed'),
        ('direct_assigned_by_hr', 'Direct Assigned by HR'),
        ('recommendation_cancelled', 'Recommendation Cancelled'),
    )

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    recommendation = models.ForeignKey(Recommendation, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} at {self.timestamp}"
    
    
################################################
# PublicApplication Model
class PublicApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
        ('hired', 'Hired'),
    )

    # applicant identity
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)

    # what they applied for (reuse Role)
    recommended_role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True)

    # resume / attachments
    resume = models.FileField(
        upload_to='public_applications/resumes/',
        validators=[validate_resume_file],
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True, null=True)

    # lifecycle and admin fields
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='public_applications_created')  # usually null for web
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # optional single-use onboarding token (you can reuse same flow later)
    token = models.CharField(max_length=100, unique=True, blank=True, null=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    token_used = models.BooleanField(default=False)

    ONBOARDING_TOKEN_TTL_DAYS = 7

    def _ensure_token(self):
        if not self.token:
            self.token = str(uuid.uuid4())
        if not self.token_expires_at:
            self.token_expires_at = timezone.now() + timedelta(days=self.ONBOARDING_TOKEN_TTL_DAYS)

    def token_is_valid(self):
        if not self.token or self.token_used:
            return False
        if self.token_expires_at and timezone.now() > self.token_expires_at:
            return False
        return True

    def mark_token_used(self):
        self.token_used = True
        self.token_expires_at = timezone.now()
        self.status = 'shortlisted'  # or another state you prefer
        self.save(update_fields=['token_used', 'token_expires_at', 'status'])

    def save(self, *args, **kwargs):
        # ensure token defaults exist only when needed (optional)
        if not self.token:
            self.token = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} — {self.recommended_role or 'Applicant'} ({self.status})"



# ---------------------------
# HR operational models
# ---------------------------
class Complaint(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints_created')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints_assigned')
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='open')
    resolution_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"


class Message(models.Model):
    """
    Simple messaging entity for HR -> employee or HR -> branch communications.
    scope: 'employee' or 'branch'
    """
    SCOPE_CHOICES = [
        ('employee', 'Employee'),
        ('branch', 'Branch'),
    ]

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages_sent')
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages_received')
    branch = models.ForeignKey('branches.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} -> {self.scope}"


class OnboardingTask(models.Model):
    """
    Basic onboarding task attached to a PublicApplication (or Recommendation later).
    """
    application = models.ForeignKey('PublicApplication', on_delete=models.CASCADE, related_name='onboarding_tasks')
    title = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    due_date = models.DateField(null=True, blank=True)
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['done', 'due_date', '-created_at']

    def __str__(self):
        return f"{self.title} ({'done' if self.done else 'pending'})"


class PayrollRecord(models.Model):
    """
    Minimal payroll record for HR bookkeeping. Keep sensitive handling in mind.
    """
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payroll_records')
    period_start = models.DateField()
    period_end = models.DateField()
    gross = models.DecimalField(max_digits=12, decimal_places=2)
    net = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_start']

    def __str__(self):
        return f"{self.employee} — {self.period_start} to {self.period_end}"


class PerformanceReview(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='performance_reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_written')
    review_date = models.DateField()
    score = models.IntegerField(null=True, blank=True)
    summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-review_date']

    def __str__(self):
        return f"Review: {self.employee} ({self.review_date})"


class TrainingSession(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(null=True, blank=True)
    attendees = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='training_sessions')
    materials = models.FileField(upload_to='training_materials/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} — {self.date or 'TBD'}"
