# Human_Resources/admin.py

from django.contrib import admin

from .models import (
    Department,
    Role,
    Permission,
    RolePermission,
    UserProfile,
    Recommendation,
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


# ============================================================
# User / HR Admins
# ============================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "department", "managed_branch")
    list_filter = ("role", "department")
    search_fields = ("user__employee_email",)


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "email",
        "recommended_role",
        "status",
        "branch",
        "created_at",
    )
    list_filter = ("status", "recommended_role", "branch")
    search_fields = ("first_name", "last_name", "email")
    ordering = ("-created_at",)


# ============================================================
# Audit / Logs
# ============================================================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "timestamp")
    list_filter = ("action",)
    search_fields = ("details",)
    ordering = ("-timestamp",)
