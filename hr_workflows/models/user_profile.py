from django.db import models
from django.conf import settings
from Human_Resources.models.role import Role
from Human_Resources.models.department import Department

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