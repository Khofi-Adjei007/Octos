# Human_Resources/api/views/recruitment_transition.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import get_object_or_404

from hr_workflows.models import RecruitmentApplication
from Human_Resources.services.query_scope import scoped_recruitment_queryset
from Human_Resources.recruitment_services.transitions import RecruitmentEngine
from Human_Resources.recruitment_services.exceptions import InvalidTransition
from Human_Resources.recruitment_services.permissions import RecruitmentPermissions
from Human_Resources.api.serializers.recruitment_detail import RecruitmentDetailSerializer


# =====================================================
# ACTION → PERMISSION MAP
# Every action requires a specific permission code.
# No action is executable without the right role.
# =====================================================

ACTION_PERMISSION_MAP = {
    "start_screening":     RecruitmentPermissions.ADVANCE,
    "schedule_interview":  RecruitmentPermissions.ADVANCE,
    "complete_interview":  RecruitmentPermissions.ADVANCE,
    "submit_final_review": RecruitmentPermissions.ADVANCE,
    "approve":             RecruitmentPermissions.HIRE,
    "reject":              RecruitmentPermissions.HIRE,
    "accept_offer":        RecruitmentPermissions.HIRE,
    "decline_offer":       RecruitmentPermissions.HIRE,
    "withdraw_offer":      RecruitmentPermissions.HIRE,
}


def user_has_recruitment_permission(user, permission_code):
    """
    Returns True if the user holds any authority role
    that grants the given permission code.
    Superusers bypass all checks.
    """
    if user.is_superuser:
        return True

    return user.authority_roles.filter(
        permissions__code=permission_code,
        permissions__is_active=True,
    ).exists()


class RecruitmentTransitionAPI(APIView):
    """
    Recruitment Transition Endpoint

    This layer does NOT contain business logic.
    It delegates entirely to RecruitmentEngine.

    Security layers in order:
    1. Must be authenticated
    2. Must have scope access to the application (query scope)
    3. Must have role permission for the specific action
    4. RecruitmentEngine enforces stage/state validity
    5. Every successful transition is written to AuditLog
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):

        # Layer 1 — Scope: can this user see this application at all?
        queryset = scoped_recruitment_queryset(request.user)
        application = get_object_or_404(queryset, pk=pk)

        action = request.data.get("action")

        if not action:
            return Response(
                {"detail": "Action is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Layer 2 — Action validity: is this a known action?
        required_permission = ACTION_PERMISSION_MAP.get(action)
        if required_permission is None:
            return Response(
                {"detail": f"Unknown action '{action}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Layer 3 — Permission: does this user's role allow this action?
        if not user_has_recruitment_permission(request.user, required_permission):
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Layer 4 — Business logic: is this transition valid at this stage?
        try:
            RecruitmentEngine.perform_action(
                application=application,
                action=action,
                actor=request.user,
                payload=request.data,
            )
        except InvalidTransition as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application.refresh_from_db()

        serializer = RecruitmentDetailSerializer(
            application,
            context={"request": request},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)