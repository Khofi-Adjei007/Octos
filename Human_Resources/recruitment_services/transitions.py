# human_resources/recruitment_services/transitions.py

from django.utils import timezone

from Human_Resources.constants import RecruitmentStatus
from Human_Resources.recruitment_services.exceptions import InvalidTransition


TRANSITIONS = {
    RecruitmentStatus.SUBMITTED: {
        "screen": RecruitmentStatus.SCREENING,
        "reject": RecruitmentStatus.REJECTED,
    },
    RecruitmentStatus.SCREENING: {
        "interview": RecruitmentStatus.INTERVIEW,
        "reject": RecruitmentStatus.REJECTED,
    },
    RecruitmentStatus.INTERVIEW: {
        "approve": RecruitmentStatus.APPROVED,
        "reject": RecruitmentStatus.REJECTED,
    },
    RecruitmentStatus.APPROVED: {
        "hire": RecruitmentStatus.ONBOARDED,
    },
}


def can_transition(current_status, action) -> bool:
    """
    Pure check.
    No side effects.
    """
    return action in TRANSITIONS.get(current_status, {})


def apply_transition(application, action):
    """
    The only function allowed to mutate application.status.
    """
    current = application.status

    if not can_transition(current, action):
        raise InvalidTransition(
            f"Cannot '{action}' from state '{current}'."
        )

    application.status = TRANSITIONS[current][action]

    if application.is_terminal():
        application.closed_at = timezone.now()

    application.save(update_fields=["status", "closed_at"])
