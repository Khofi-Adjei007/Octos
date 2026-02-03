# employees/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Employee


def model_has_field(model, name):
    return any(f.name == name for f in model._meta.get_fields())


@admin.register(Employee)
class EmployeeAdmin(BaseUserAdmin):
    model = Employee

    list_display = ("employee_email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "department")
    search_fields = ("employee_email", "first_name", "last_name")
    ordering = ("employee_email",)

    readonly_fields = tuple(
        name for name in ("created_at", "approved_at")
        if model_has_field(Employee, name)
    )

    fieldsets = (
        (_("Login"), {"fields": ("employee_email", "password")}),
        (_("Personal info"), {
            "fields": (
                "first_name",
                "middle_name",
                "last_name",
                "phone_number",
                "profile_picture",
            )
        }),
        (_("Work"), {
            "fields": (
                "position_title",
                "department",
                "branch",
                "manager",
            )
        }),
        (_("Permissions"), {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        (_("Important dates"), {
            "fields": ("approved_at", "created_at")
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "employee_email",
                "first_name",
                "last_name",
                "password1",
                "password2",
                "is_staff",
                "is_active",
            ),
        }),
    )
