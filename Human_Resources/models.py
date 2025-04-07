# Human_Resources/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid

# Validator for PDF files
def validate_pdf_file(value):
    if not value.name.endswith('.pdf'):
        raise ValidationError('Only PDF files are allowed.')
    if value.size > 10 * 1024 * 1024:  # 10MB limit
        raise ValidationError('File size must be less than 10MB.')

# Role Model
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# UserProfile Model
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='userprofile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.CharField(max_length=50, blank=True)  # Matches Employee.department
    managed_branch = models.ForeignKey('branches.Branch', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Profile for {self.user}"

# Updated Recommendation Model
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
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )

    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    recommended_role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    branch = models.ForeignKey('branches.Branch', on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    resume = models.FileField(upload_to='recommendation_resumes/', validators=[validate_pdf_file], null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    token = models.CharField(max_length=100, unique=True, blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='recommendations_made')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Recommendation for {self.first_name} {self.last_name} - {self.status}"

# AuditLog Model
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    recommendation = models.ForeignKey(Recommendation, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} at {self.timestamp}"