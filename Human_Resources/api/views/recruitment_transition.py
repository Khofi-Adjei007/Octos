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
from Human_Resources.api.views._notify_helpers import get_hr_managers, user_display
from notifications.services import notify, notify_many


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

# Human-readable label for each action used in notification messages
ACTION_LABEL_MAP = {
    "start_screening":     "moved to Screening",
    "schedule_interview":  "scheduled for Interview",
    "complete_interview":  "completed Interview",
    "submit_final_review": "moved to Final Review",
    "approve":             "approved for hire",
    "reject":              "rejected",
    "accept_offer":        "accepted the offer",
    "decline_offer":       "declined the offer",
    "withdraw_offer":      "had their offer withdrawn",
}


def user_has_recruitment_permission(user, permission_code):
    if user.is_superuser:
        return True
    return user.authority_roles.filter(
        permissions__code=permission_code,
        permissions__is_active=True,
    ).exists()


class RecruitmentTransitionAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):

        queryset = scoped_recruitment_queryset(request.user)
        application = get_object_or_404(queryset, pk=pk)

        action = request.data.get("action")

        if not action:
            return Response(
                {"detail": "Action is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        required_permission = ACTION_PERMISSION_MAP.get(action)
        if required_permission is None:
            return Response(
                {"detail": f"Unknown action '{action}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user_has_recruitment_permission(request.user, required_permission):
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )

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

        # --- Notify ---
        applicant_name = str(application.applicant)
        action_label   = ACTION_LABEL_MAP.get(action, action.replace("_", " "))
        message        = f"{applicant_name} has been {action_label} by {user_display(request.user)}."
        link           = f"/hr/api/applications/{application.pk}/"

        recipients = get_hr_managers(excluding=request.user)

        # Also notify assigned reviewer if different from actor
        reviewer = application.assigned_reviewer
        if reviewer and reviewer.pk != request.user.pk:
            recipients.append(reviewer)

        notify_many(
            recipients=recipients,
            verb="stage_changed",
            message=message,
            link=link,
            actor=request.user,
        )

        serializer = RecruitmentDetailSerializer(
            application,
            context={"request": request},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)