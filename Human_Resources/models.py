# Human_Resources/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

User = get_user_model()

# Validate that the uploaded file is a PDF
def validate_pdf_file(value):
    if not value.name.endswith('.pdf'):
        raise ValidationError('Only PDF files are allowed.')
    if value.size > 10 * 1024 * 1024:  # 10MB limit
        raise ValidationError('File size must be less than 10MB.')

# Role Model (still needed for role-based access control)
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., "Branch Manager", "Employee", "HR"
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Existing UserProfile Model (aligned with Employee model)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    managed_branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manager_userprofile'
    )
    department = models.CharField(max_length=50, blank=True, null=True)
    # Additional fields for registration process (aligned with Employee)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    employee = models.OneToOneField(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_profile'
    )  # Link to Employee model
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role.name if self.role else 'No Role'}"

# Updated Recommendation Model
class Recommendation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    recommended_role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    branch = models.ForeignKey('branches.Branch', on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    resume = models.FileField(upload_to='recommendation_resumes/', validators=[validate_pdf_file], null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    form_url = models.CharField(max_length=255, blank=True)
    form_url_expiry = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recommendations_made')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recommendation for {self.first_name} {self.last_name} - {self.status}"

# Audit Log Model
class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('recommendation_created', 'Recommendation Created'),
        ('recommendation_approved', 'Recommendation Approved'),
        ('recommendation_rejected', 'Recommendation Rejected'),
        ('form_submitted', 'Form Submitted'),
        ('application_approved', 'Application Approved'),
        ('first_login', 'First Login'),
        ('password_reset', 'Password Reset'),
    )

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    recommendation = models.ForeignKey(Recommendation, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} at {self.timestamp}"