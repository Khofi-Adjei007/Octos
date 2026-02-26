# employees/auth/context.py
from employees.models import Employee
from employees.auth.permissions import employee_has_permission
from Human_Resources.models.authority import AuthorityAssignment


class EmployeeContext:
    def __init__(self, employee: Employee):
        self.employee = employee
        self.employee_pk = employee.pk
        self.employee_id = employee.employee_id

        self.is_active = employee.is_active
        self.employment_status = employee.employment_status
        self.deleted_at = employee.deleted_at

        self._assignment = (
            AuthorityAssignment.objects
            .filter(user=employee, is_active=True)
            .select_related('role', 'branch')
            .first()
        )
        self.role_code = self._assignment.role.code if self._assignment and self._assignment.role else None
        self.branch_id = self._assignment.branch_id if self._assignment else employee.branch_id
        self.role_id = self._assignment.role_id if self._assignment else employee.role_id
        self.primary_role = self.role_code

    @property
    def is_active_employee(self) -> bool:
        if not self.is_active:
            return False
        if self.deleted_at is not None:
            return False
        if self.employment_status != "ACTIVE":
            return False
        return True

    @property
    def can_access_multiple_branches(self) -> bool:
        return any(
            employee_has_permission(self.employee, perm)
            for perm in ("manage_multiple_branches", "view_all_branches", "regional_access")
        )