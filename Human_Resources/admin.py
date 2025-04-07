# Human_Resources/admin.py
from django.contrib import admin
from .models import Role, UserProfile, Recommendation, AuditLog

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