from django.db import models
from django.contrib.auth import get_user_model


# Create your models here.


User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    managed_branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manager_userprofile'  # Unique name to avoid conflict
    )
    department = models.CharField(max_length=50, blank=True, null=True)



class HiringRecommendation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    employee = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='recommendations')
    branch_manager = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        related_name='recommendations_made'
    )
    recommended_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    hr_manager = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommendations_approved'
    )
    hr_action_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Recommendation for {self.employee} by {self.branch_manager}"