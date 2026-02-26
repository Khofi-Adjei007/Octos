# employees/services/activation.py

import logging
import secrets
import string

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


class ActivationError(Exception):
    pass


class AccountActivationService:
    """
    Activates an employee account after onboarding Phase 3.

    Responsibilities:
    - Set employee_email from applicant email
    - Generate secure temporary password
    - Create AuthorityAssignment (role + branch)
    - Set must_change_password = True
    - Return activation payload for welcome email

    Does NOT send email — that is the caller's responsibility.
    """

    @classmethod
    @transaction.atomic
    def activate(cls, employee, application) -> dict:
        """
        Main entry point. Call after Employee record is created.

        Returns:
            {
                "employee_email": str,
                "temp_password": str,
                "branch": Branch | None,
                "role": AuthorityRole | None,
            }
        """
        # 1. Set employee_email from applicant email
        cls._set_employee_email(employee, application)

        # 2. Generate temporary password
        temp_password = cls._generate_temp_password()
        employee.set_password(temp_password)
        employee.must_change_password = True
        employee.approved_at = timezone.now()
        employee.save(update_fields=[
            "employee_email",
            "password",
            "must_change_password",
            "approved_at",
        ])

        # 3. Create AuthorityAssignment
        authority_role, branch = cls._create_authority_assignment(employee, application)

        # 4. Generate employee ID
        from employees.services.employee_id import EmployeeIDService
        try:
            job_offer = application.job_offer
            hire_year = job_offer.start_date.year if job_offer and job_offer.start_date else None
        except Exception:
            hire_year = None

        EmployeeIDService.generate(
            employee=employee,
            branch=application.recommended_branch,
            hire_year=hire_year,
        )

        logger.info(
            "AccountActivationService: activated employee %s | role=%s | branch=%s | id=%s",
            employee.employee_email,
            authority_role.code if authority_role else None,
            branch.name if branch else None,
            employee.employee_id,
        )

        return {
            "employee_email": employee.employee_email,
            "temp_password": temp_password,
            "branch": branch,
            "role": authority_role,
        }

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------

    @staticmethod
    def _set_employee_email(employee, application):
        """Use applicant email as the login email."""
        email = getattr(application.applicant, "email", None)
        if not email:
            raise ActivationError("Applicant has no email address.")

        from employees.models import Employee
        if Employee.objects.filter(employee_email=email).exclude(pk=employee.pk).exists():
            raise ActivationError(
                f"Email {email} is already in use by another employee account."
            )

        employee.employee_email = email

    @staticmethod
    def _generate_temp_password(length=12) -> str:
        """
        Generate a secure temporary password.
        Format: 3 uppercase + 3 lowercase + 3 digits + 3 symbols
        Always meets common password policy requirements.
        """
        upper = secrets.choice(string.ascii_uppercase)
        lower = secrets.choice(string.ascii_lowercase)
        digit = secrets.choice(string.digits)
        symbol = secrets.choice("@#$%&*")

        # Fill remaining length with mixed characters
        alphabet = string.ascii_letters + string.digits + "@#$%&*"
        rest = [secrets.choice(alphabet) for _ in range(length - 4)]

        # Shuffle to avoid predictable pattern
        password_chars = list(upper + lower + digit + symbol) + rest
        secrets.SystemRandom().shuffle(password_chars)
        return "".join(password_chars)

    @staticmethod
    def _create_authority_assignment(employee, application):
        """
        Look up AuthorityRole via RoleMapping and create AuthorityAssignment.
        Fails loudly if mapping is missing — no silent fallbacks.
        """
        from Human_Resources.models import RoleMapping
        from Human_Resources.models.authority import AuthorityAssignment

        role_title = application.role_applied_for
        branch = application.recommended_branch

        # Look up role mapping
        try:
            mapping = RoleMapping.objects.select_related("authority_role").get(
                role_title=role_title,
                is_active=True,
            )
        except RoleMapping.DoesNotExist:
            raise ActivationError(
                f"No active RoleMapping found for role title: '{role_title}'. "
                f"Add it via the HR admin panel before activating this employee."
            )

        authority_role = mapping.authority_role

        # Determine scope type from role's allowed scopes
        allowed = authority_role.allowed_scopes or []
        if "BRANCH" in allowed and branch:
            scope_type = "BRANCH"
        elif "REGION" in allowed:
            scope_type = "REGION"
        elif "BELT" in allowed:
            scope_type = "BELT"
        else:
            scope_type = "GLOBAL"

        # Deactivate any existing assignments
        AuthorityAssignment.objects.filter(user=employee, is_active=True).update(is_active=False)

        # Create new assignment
        assignment = AuthorityAssignment(
            user=employee,
            role=authority_role,
            scope_type=scope_type,
            is_active=True,
        )

        if scope_type == "BRANCH":
            assignment.branch = branch
        elif scope_type == "REGION":
            assignment.region = getattr(branch, "region", None)

        assignment.full_clean()
        assignment.save()

        return authority_role, branch