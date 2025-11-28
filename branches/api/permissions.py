from rest_framework.permissions import BasePermission, SAFE_METHODS

# Helper role-checks: adjust to your actual project logic (e.g., profile flags, groups)
def _is_ceo(user):
    if not user or not user.is_authenticated:
        return False
    # try common patterns; adapt to your user model
    if getattr(user, "is_superuser", False):
        return True
    if getattr(user, "is_ceo", False):
        return True
    if user.groups.filter(name__iexact="ceo").exists():
        return True
    return False

class IsSuperuserOrReadOnly(BasePermission):
    """
    SAFE methods allowed for any authenticated user (or you can allow anonymous).
    Creation/deletion restricted to superuser/CEO.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return _is_ceo(request.user)

class IsBranchManagerOrSuperuser(BasePermission):
    """
    For object-level edits: allow if superuser/CEO OR the user is the branch manager.
    Assumes request.user has a related Employee object accessible via 'employee' attribute,
    where Employee.managed_branch relates to Branch.
    Adapt this to your real employee->user relation.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if _is_ceo(user):
            return True
        # quick safe-check: if the user has employee and manages this branch
        employee = getattr(user, "employee", None)
        if employee is None:
            # try a different attribute name if your project uses profile or staff
            employee = getattr(user, "staff_profile", None)
        try:
            if employee and getattr(employee, "managed_branch_id", None) == obj.pk:
                return True
        except Exception:
            pass
        return False
