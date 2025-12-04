from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from branches.models import Branch

def is_branch_manager(user, branch):
    if not user or not user.is_authenticated:
        return False
    # direct OneToOne manager relation on Branch
    try:
        if getattr(branch, "manager_id", None) and branch.manager_id == getattr(user, "pk", None):
            return True
    except Branch.DoesNotExist:
        return False
    # group fallback
    if user.groups.filter(name="Branch Managers").exists():
        return True
    # superusers and staff may pass
    if user.is_superuser or user.is_staff:
        return True
    return False

def require_branch_manager(user, branch_pk):
    branch = get_object_or_404(Branch, pk=branch_pk)
    if not is_branch_manager(user, branch):
        raise PermissionDenied
    return branch
