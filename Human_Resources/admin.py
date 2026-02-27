# Human_Resources/admin.py

from django.contrib import admin
from Human_Resources.models.job_position import JobPosition
from Human_Resources.models import (
    Department,
    Role,
    Permission,
    AuditLog,
)


# ============================================================
# Core Reference Admins
# ============================================================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "created_at")
    search_fields = ("code", "name")
    ordering = ("name",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "default_pay_grade")
    search_fields = ("name", "code")
    ordering = ("name",)


# ============================================================
# Authorization Admins
# ============================================================

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "created_at")
    search_fields = ("code", "name")
    list_filter = ("is_active",)
    ordering = ("code",)


# ============================================================
# Audit / Logs
# ============================================================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["action", "user", "content_type", "object_id", "ip_address", "timestamp"]
    list_filter = ["action", "content_type"]
    search_fields = ["details", "user__email", "user__username"]
    ordering = ["-timestamp"]
    readonly_fields = [
        "action",
        "user",
        "content_type",
        "object_id",
        "details",
        "ip_address",
        "user_agent",
        "timestamp",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

from Human_Resources.models.authority import AuthorityRole, AuthorityAssignment, RoleMapping


@admin.register(RoleMapping)
class RoleMappingAdmin(admin.ModelAdmin):
    list_display = ("role_title", "authority_role", "is_active", "created_at")
    list_filter = ("is_active", "authority_role")
    search_fields = ("role_title",)
    ordering = ("role_title",)


@admin.register(AuthorityRole)
class AuthorityRoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_system_role")
    search_fields = ("code", "name")
    filter_horizontal = ("permissions",)


@admin.register(AuthorityAssignment)
class AuthorityAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "scope_type", "branch", "region", "is_active", "created_at")
    list_filter = ("scope_type", "is_active", "role")
    search_fields = ("user__employee_email", "role__code")


@admin.register(JobPosition)
class JobPositionAdmin(admin.ModelAdmin):
    list_display  = ("title", "code", "department", "is_active", "created_at")
    list_filter   = ("is_active", "department")
    search_fields = ("title", "code")
    ordering      = ("title",)