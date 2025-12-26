# employees/auth/permissions.py

from Human_Resources.models import RolePermission


def employee_has_permission(employee, permission_code: str) -> bool:
    """
    Returns True if the employee's role grants the given permission.

    This function is intentionally explicit and database-backed.
    Caching can be added later without changing call sites.
    """

    if not employee.role_id:
        return False

    return RolePermission.objects.filter(
        role_id=employee.role_id,
        permission__code=permission_code,
        permission__is_active=True
    ).exists()
