# public/api/permissions.py
from rest_framework.permissions import BasePermission

class IsHR(BasePermission):
    """
    Allow only users in HR group or with is_staff/is_superuser.
    Adjust to your Role/Group setup.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        return user.groups.filter(name__iexact="HR").exists()
