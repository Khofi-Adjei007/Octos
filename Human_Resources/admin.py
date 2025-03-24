from django.contrib import admin

# Register your models here.
# Human_Resources/admin.py
from django.contrib import admin
from .models import Role, UserProfile, Recommendation, AuditLog

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'managed_branch', 'department', 'employee')
    search_fields = ('user__username',)
    list_filter = ('role', 'managed_branch', 'department')

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'status', 'created_by', 'created_at', 'resume')
    list_filter = ('status', 'branch', 'recommended_role')
    search_fields = ('first_name', 'last_name', 'email')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'timestamp')
    list_filter = ('action',)
    search_fields = ('details',)