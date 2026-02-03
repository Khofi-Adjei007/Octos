# Human_Resources/admin.py

from django.contrib import admin

from Human_Resources.models import (
    Department,
    Role,
    Permission,
    RolePermission,
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


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "permission", "granted_at")
    list_filter = ("role",)
    search_fields = ("role__name", "permission__code")
    ordering = ("role__name",)


#


# ============================================================
# Audit / Logs
# ============================================================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "timestamp")
    list_filter = ("action",)
    search_fields = ("details",)
    ordering = ("-timestamp",)
