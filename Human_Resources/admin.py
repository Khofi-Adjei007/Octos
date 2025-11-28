# Human_Resources/admin.py
from django.contrib import admin
from .models import Role, UserProfile, Recommendation, AuditLog, PublicApplication, Department

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'department', 'managed_branch']  # Changed 'employee' to 'user'
    list_filter = ['role', 'department']
    search_fields = ['user__employee_email', 'department']

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'recommended_role', 'status', 'created_by']
    list_filter = ['status', 'recommended_role']
    search_fields = ['first_name', 'last_name', 'email']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'recommendation', 'timestamp']
    list_filter = ['action']
    search_fields = ['details']


@admin.register(PublicApplication)
class PublicApplicationAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "recommended_role", "status", "created_at")
    list_filter = ("status", "recommended_role")
    search_fields = ("first_name", "last_name", "email", "phone")
    readonly_fields = ("created_at", "updated_at")

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'created_at')
    search_fields = ('code', 'name')


