# Human_Resources/services/authority.py

from Human_Resources.models.authority import AuthorityAssignment, AuthorityRole
from Human_Resources.models.permission import Permission


def has_authority(user, permission_code, *, branch=None, region=None, belt=None):
    """
    Check if a user has a given permission within the specified scope.
    """

    # Super Admin short-circuit
    if user.is_superuser:
        return True

    try:
        permission = Permission.objects.get(code=permission_code, is_active=True)
    except Permission.DoesNotExist:
        return False

    assignments = (
        AuthorityAssignment.objects
        .select_related("role", "belt", "region", "branch")
        .filter(
            user=user,
            is_active=True,
            role__permissions=permission,
        )
    )

    for assignment in assignments:
        scope = assignment.scope_type

        # GLOBAL
        if scope == AuthorityRole.SCOPE_GLOBAL:
            return True

        # BELT
        if scope == AuthorityRole.SCOPE_BELT and belt:
            if assignment.belt_id == belt.id:
                return True

        # REGION
        if scope == AuthorityRole.SCOPE_REGION and region:
            if assignment.region_id == region.id:
                return True

        # BRANCH
        if scope == AuthorityRole.SCOPE_BRANCH and branch:
            if assignment.branch_id == branch.id:
                return True

    return False
