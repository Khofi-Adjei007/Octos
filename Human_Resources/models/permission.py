from django.db import models
from Human_Resources.models.role import Role

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
