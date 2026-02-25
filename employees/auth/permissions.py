# employees/auth/permissions.py
from Human_Resources.models import RolePermission, Role
from Human_Resources.models.authority import AuthorityAssignment


def employee_has_permission(employee, permission_code: str) -> bool:
    assignment = (
        AuthorityAssignment.objects
        .filter(user=employee, is_active=True)
        .select_related('role')
        .first()
    )

    if not assignment or not assignment.role:
        return False

    # AuthorityAssignment.role is AuthorityRole — bridge to Role via name match
    role = Role.objects.filter(name=assignment.role.name).first()
    if not role:
        return False

    return RolePermission.objects.filter(
        role=role,
        permission__code=permission_code,
        permission__is_active=True
    ).exists()