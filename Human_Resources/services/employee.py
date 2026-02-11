# Human_Resources/services/employee.py

from django.core.exceptions import PermissionDenied
from django.db import transaction

from Human_Resources.services.authority import has_authority
from employees.models import Employee


def _employee_scope(employee):
    """
    Resolve scope objects for an employee.
    """
    branch = employee.branch
    region = branch.region if branch else None
    belt = region.belt if region else None

    return branch, region, belt


@transaction.atomic
def create_employee(*, user, employee_data):
    """
    Create a new employee with authority enforcement.
    """

    branch = employee_data.get("branch")
    region = branch.region if branch else None
    belt = region.belt if region else None

    if not has_authority(
        user,
        "employee.create",
        region=region,
        belt=belt,
    ):
        raise PermissionDenied(
            "You do not have authority to create employees in this region."
        )

    employee = Employee.objects.create(**employee_data)
    return employee


@transaction.atomic
def update_employee(*, user, employee, updates):
    """
    Update an existing employee with authority enforcement.
    """

    branch, region, belt = _employee_scope(employee)

    if not has_authority(
        user,
        "employee.update",
        region=region,
        belt=belt,
    ):
        raise PermissionDenied(
            "You do not have authority to update this employee."
        )

    for field, value in updates.items():
        setattr(employee, field, value)

    employee.save()
    return employee


@transaction.atomic
def deactivate_employee(*, user, employee):
    """
    Deactivate (soft-delete) an employee with authority enforcement.
    """

    branch, region, belt = _employee_scope(employee)

    if not has_authority(
        user,
        "employee.deactivate",
        region=region,
        belt=belt,
    ):
        raise PermissionDenied(
            "You do not have authority to deactivate this employee."
        )

    employee.soft_delete(by_user=user)
    return employee
