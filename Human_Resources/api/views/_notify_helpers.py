# Human_Resources/api/views/_notify_helpers.py
"""
Shared helpers for resolving notification recipients.
Import from any HR API view — never instantiate directly.
"""
from django.contrib.auth import get_user_model

User = get_user_model()


def get_hr_managers(excluding=None):
    """
    Returns all active employees with an HR authority role assignment.
    Excludes `excluding` user if provided (e.g. the actor themselves).
    """
    from Human_Resources.models.authority import AuthorityAssignment
    qs = User.objects.filter(
        is_active=True,
        authority_assignments__is_active=True,
        authority_assignments__role__code__icontains="HR",
    ).distinct()
    if excluding:
        qs = qs.exclude(pk=excluding.pk)
    return list(qs)


def get_branch_manager(branch):
    """
    Returns the active branch manager for a given branch, or None.
    """
    if not branch:
        return None
    from Human_Resources.models.authority import AuthorityAssignment
    assignment = (
        AuthorityAssignment.objects
        .filter(
            branch=branch,
            is_active=True,
            role__code="BRANCH_MANAGER",
        )
        .select_related("user")
        .first()
    )
    return assignment.user if assignment else None


def user_display(u):
    """Safe display name for any user model."""
    if u is None:
        return "System"
    fn = getattr(u, "get_full_name", None)
    name = fn() if callable(fn) else None
    return name if name else u.get_username()