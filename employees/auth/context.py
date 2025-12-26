# employees/auth/context.py

from employees.models import Employee
from employees.auth.permissions import employee_has_permission


class EmployeeContext:
    """
    Derived, read-only context for the authenticated employee.

    This object answers:
    - Who is acting?
    - Where (branch)?
    - Under what employment state?

    It MUST be cheap to reconstruct and must never persist state.
    """

    def __init__(self, employee: Employee):
        self.employee = employee

        # Identity
        self.employee_pk = employee.pk
        self.employee_id = employee.employee_id

        # Org scope
        self.branch_id = employee.branch_id
        self.role_id = employee.role_id
        self.primary_role = employee.primary_role

        # Status
        self.is_active = employee.is_active
        self.employment_status = employee.employment_status
        self.deleted_at = employee.deleted_at

    @property
    def is_active_employee(self) -> bool:
        """
        Canonical check for whether an employee is allowed to act.
        """
        if not self.is_active:
            return False

        if self.deleted_at is not None:
            return False

        if self.employment_status != "ACTIVE":
            return False

        return True

    @property
    def can_access_multiple_branches(self) -> bool:
        """
        Whether this employee can operate across multiple branches.
        Typically true for:
        - CEO
        - Regional HR
        - Senior managers
        """
        return any(
            employee_has_permission(self.employee, perm)
            for perm in (
                "manage_multiple_branches",
                "view_all_branches",
                "regional_access",
            )
        )
