# employees/auth/permissions.py
from Human_Resources.models.authority import AuthorityAssignment


def employee_has_permission(employee, permission_code: str) -> bool:
    assignment = (
        AuthorityAssignment.objects
        .filter(user=employee, is_active=True)
        .select_related('role')
        .prefetch_related('role__permissions')
        .first()
    )

    if not assignment or not assignment.role:
        return False

    return assignment.role.permissions.filter(
        code=permission_code,
        is_active=True
    ).exists()