# Human_Resources/services/recruitment.py
from django.core.exceptions import PermissionDenied
from django.db import transaction
from Human_Resources.services.authority import has_authority
from Human_Resources.constants import RecruitmentSource
from hr_workflows.models import RecruitmentApplication


@transaction.atomic
def approve_application(*, user, application):
    """
    Approve a recruitment application with full authority enforcement.
    """

    region = application.region
    belt = region.belt

    if not has_authority(
        user,
        "recruitment.approve",
        region=region,
        belt=belt,
    ):
        raise PermissionDenied(
            "You do not have authority to approve applications in this scope."
        )

    application.status = "APPROVED"
    application.approved_by = user
    application.save(update_fields=["status", "approved_by"])



# Note: The recommend_candidate function is designed to be called from the API view, which already checks for authentication.
# The authority check within the function ensures that only users with the appropriate permissions can recommend candidates,
# even if they are authenticated.
@transaction.atomic
def recommend_candidate(*, user, applicant, role_applied_for):
    """
    Recommend a candidate with scoped authority enforcement.
    """

    branch = getattr(user, "branch", None)
    region = branch.region if branch else None
    belt = region.belt if region else None

    if not has_authority(
        user,
        "recruitment.review",
        branch=branch,
        region=region,
        belt=belt,
    ):
        raise PermissionDenied(
            "You do not have authority to recommend candidates."
        )

    application = RecruitmentApplication.objects.create(
        applicant=applicant,
        role_applied_for=role_applied_for,
        source=RecruitmentSource.RECOMMENDATION,
        recommended_by=user,
        recommended_branch=branch,
        status=RecruitmentApplication._meta.get_field("status").default,
    )

    return application
