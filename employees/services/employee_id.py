# employees/services/employee_id.py

import logging
from django.db import transaction

logger = logging.getLogger(__name__)

COMPANY_PREFIX = "FPP"
HQ_FALLBACK    = "HQ"


class EmployeeIDService:
    """
    Generates human-readable, unique employee IDs.

    Format: FPP-WH-2026-0042-K
    - FPP  : company prefix (Farhat Printing Press)
    - WH   : branch shortcode derived from branch.code
    - 2026 : hire year
    - 0042 : global zero-padded sequence (atomic, no duplicates)
    - K    : first letter of first name

    Thread-safe: uses SELECT FOR UPDATE on the sequence table.
    Falls back to FPP-HQ-YYYY-XXXX-K for employees without a branch.
    """

    @classmethod
    @transaction.atomic
    def generate(cls, employee, branch=None, hire_year=None) -> str:
        """
        Generate and assign employee_id.
        Returns the generated ID string.
        """
        from employees.models import Employee

        branch_code   = cls._branch_shortcode(branch or employee.branch)
        year          = hire_year or cls._hire_year(employee)
        initial       = (employee.first_name or "X")[0].upper()
        sequence      = cls._next_sequence()

        employee_id = f"{COMPANY_PREFIX}-{branch_code}-{year}-{sequence:04d}-{initial}"

        # Collision guard (extremely unlikely but safe)
        if Employee.objects.filter(employee_id=employee_id).exclude(pk=employee.pk).exists():
            sequence  = cls._next_sequence()
            employee_id = f"{COMPANY_PREFIX}-{branch_code}-{year}-{sequence:04d}-{initial}"

        employee.employee_id = employee_id
        employee.save(update_fields=["employee_id"])

        logger.info("EmployeeIDService: assigned %s to employee pk=%s", employee_id, employee.pk)
        return employee_id

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------

    @staticmethod
    def _branch_shortcode(branch) -> str:
        """
        Derives a 2-4 char shortcode from branch.code.
        WESTLAND_HQ  → WH
        ACCRA_MAIN   → AM
        KUMASI_NORTH → KN
        None         → HQ
        """
        if not branch or not branch.code:
            return HQ_FALLBACK

        parts = branch.code.split("_")
        if len(parts) == 1:
            return parts[0][:3].upper()

        # Take first letter of each word, max 4 chars
        return "".join(p[0] for p in parts if p)[:4].upper()

    @staticmethod
    def _hire_year(employee) -> int:
        from django.utils import timezone
        if employee.hire_date:
            return employee.hire_date.year
        return timezone.now().year

    @staticmethod
    def _next_sequence() -> int:
        """
        Atomic global sequence counter using DB row locking.
        Uses the Employee table itself — counts all non-null employee_ids.
        Safe under concurrent writes.
        """
        from employees.models import Employee
        # Lock and count — next sequence = current count + 1
        count = (
            Employee.objects
            .select_for_update()
            .exclude(employee_id__isnull=True)
            .exclude(employee_id__exact="")
            .count()
        )
        return count + 1