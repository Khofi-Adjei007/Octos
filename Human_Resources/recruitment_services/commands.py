# Human_Resources/recruitment_services/commands.py

from django.db import transaction

from hr_workflows.models import applicant as Applicant, recruitment_application as RecruitmentApplication
from Human_Resources.constants import RecruitmentSource, RecruitmentStatus
from Human_Resources.recruitment_services.transitions import apply_transition
from Human_Resources.recruitment_services.exceptions import (
    RecruitmentError,
    PermissionDenied,
    HiringError,
)

def submit_public_application(*, applicant_data, role_applied_for):
    """
    Entry point for public recruitment.
    """

    with transaction.atomic():
        applicant, _ = Applicant.objects.get_or_create(
            phone=applicant_data["phone"],
            defaults={
                "first_name": applicant_data["first_name"],
                "last_name": applicant_data["last_name"],
                "email": applicant_data.get("email"),
                "national_id": applicant_data.get("national_id"),
            },
        )

        application = RecruitmentApplication.objects.create(
            applicant=applicant,
            source=RecruitmentSource.PUBLIC,
            role_applied_for=role_applied_for,
            status=RecruitmentStatus.SUBMITTED,
        )

    return application

def recommend_applicant(*, applicant, role_applied_for, actor):
    """
    Creates a recruitment application via recommendation.
    """

    if not getattr(actor, "can_recommend", False):
        raise PermissionDenied("Actor is not allowed to recommend applicants.")

    with transaction.atomic():
        application = RecruitmentApplication.objects.create(
            applicant=applicant,
            source=RecruitmentSource.RECOMMENDATION,
            recommended_by=actor,
            recommended_branch=getattr(actor, "branch", None),
            role_applied_for=role_applied_for,
            status=RecruitmentStatus.SCREENING,  # recommendation skips submitted
        )

    return application

def advance_application(*, application, action, actor):
    """
    Moves an application through the recruitment pipeline.
    """

    if not getattr(actor, "is_hr", False):
        raise PermissionDenied("Only HR may advance recruitment applications.")

    apply_transition(application, action)

    return application

def hire_applicant(*, application, actor, create_employee_callable):
    """
    Finalizes recruitment and creates an employee.
    """

    if not getattr(actor, "is_hr", False):
        raise PermissionDenied("Only HR may hire applicants.")

    if application.status != RecruitmentStatus.APPROVED:
        raise HiringError("Only approved applications can be hired.")

    if application.is_terminal():
        raise HiringError("This recruitment application is already closed.")

    with transaction.atomic():
        employee = create_employee_callable(application)
        apply_transition(application, "hire")

    return employee
