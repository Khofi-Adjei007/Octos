# employees/auth/guards.py

from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

from employees.auth.context import EmployeeContext
from employees.auth.permissions import employee_has_permission
from employees.auth.exceptions import (
    InactiveEmployeeError,
    MissingPermissionError,
)


def require_employee_login(view_func):
    """
    Ensures:
    - request.user is authenticated
    - request.user is an active Employee
    - request.employee_context is available downstream
    """

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return redirect("employeesLogin")

        context = EmployeeContext(user)

        if not context.is_active_employee:
            raise InactiveEmployeeError(
                "Employee account is inactive, suspended, or terminated."
            )

        # Attach once, reuse everywhere
        request.employee_context = context

        return view_func(request, *args, **kwargs)

    return _wrapped


def require_permission(permission_code: str):
    """
    Enforces role-based permission checks.

    Must be used AFTER require_employee_login.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            employee = request.user

            if not employee_has_permission(employee, permission_code):
                raise MissingPermissionError(
                    f"Missing required permission: {permission_code}"
                )

            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator

def require_branch_access(resolve_branch_id):
    """
    Enforces branch-level access control.

    resolve_branch_id:
        A callable that receives (request, *args, **kwargs)
        and returns the target branch_id for the request.

    Rules:
    - Superusers always pass
    - Employees with multi-branch authority pass
    - Otherwise, employee.branch_id must match target branch_id
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            context = getattr(request, "employee_context", None)

            if context is None:
                raise RuntimeError(
                    "require_branch_access must be used after require_employee_login"
                )

            # Resolve the branch being accessed
            target_branch_id = resolve_branch_id(request, *args, **kwargs)

            # No branch specified → deny
            if not target_branch_id:
                raise PermissionDenied("Branch context could not be resolved.")

            # Superusers bypass branch restriction
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Multi-branch authority (HQ / regional)
            if context.can_access_multiple_branches:
                return view_func(request, *args, **kwargs)

            # Enforce same-branch access
            if context.branch_id != target_branch_id:
                raise PermissionDenied(
                    "You are not permitted to access resources for this branch."
                )

            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator

def require_permission_any(permission_codes):
    """
    Enforces that the employee has at least ONE of the given permissions.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            employee = request.user

            for code in permission_codes:
                if employee_has_permission(employee, code):
                    return view_func(request, *args, **kwargs)

            raise MissingPermissionError(
                f"Missing required permission (one of): {', '.join(permission_codes)}"
            )

        return _wrapped

    return decorator
