# Human_Resources/api/views/recommendation.py

import logging
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from hr_workflows.models.applicant import Applicant
from hr_workflows.models.recruitment_application import RecruitmentApplication, RecruitmentStage, RecruitmentDecision
from Human_Resources.constants import RecruitmentSource
from branches.models import Branch
from Human_Resources.models.job_position import JobPosition
from notifications.services import notify_many


logger = logging.getLogger(__name__)


def _hr_managers(excluding=None):
    from employees.models import Employee
    qs = Employee.objects.filter(
        is_active=True,
        authority_assignments__is_active=True,
        authority_assignments__role__code__in=["HR_ADMIN", "BELT_HR_OVERSEER"],
    ).distinct()
    if excluding:
        qs = qs.exclude(pk=excluding.pk)
    return list(qs)

class RecommendCandidateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        data = request.data

        def user_display(u):
            fn = getattr(u, "get_full_name", None)
            name = fn() if callable(fn) else None
            return name if name else u.get_username()

        # --- Validate required fields ---
        required = ["first_name", "last_name", "phone"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not data.get("position_id") and not data.get("role_applied_for"):
            return Response(
                {"error": "Please select a position."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Resolve branch ---
        branch = getattr(request.user, "branch", None)
        branch_id = data.get("branch_id")
        if branch_id:
            try:
                branch = Branch.objects.get(pk=branch_id)
            except Branch.DoesNotExist:
                return Response({"error": "Invalid branch."}, status=status.HTTP_400_BAD_REQUEST)

        # --- Resolve position FK ---
        position = None
        position_id = data.get("position_id")
        if position_id:
            try:
                position = JobPosition.objects.get(pk=position_id, is_active=True)
            except JobPosition.DoesNotExist:
                return Response({"error": "Invalid position selected."}, status=status.HTTP_400_BAD_REQUEST)

        # --- Create Applicant ---
        applicant = Applicant.objects.create(
            first_name  = data["first_name"].strip(),
            last_name   = data["last_name"].strip(),
            phone       = data["phone"].strip(),
            email       = data.get("email", "").strip() or None,
            national_id = data.get("national_id", "").strip() or None,
            gender      = data.get("gender", "") or None,
        )

        # --- Create RecruitmentApplication ---
        application = RecruitmentApplication(
            applicant          = applicant,
            source             = RecruitmentSource.RECOMMENDATION,
            recommended_by     = request.user,
            recommended_branch = branch,
            role_applied_for   = position.title if position else data.get("role_applied_for", "").strip(),
            position           = position,
            current_stage      = RecruitmentStage.SUBMITTED,
            status             = RecruitmentDecision.ACTIVE,
            priority           = "high",
        )

        if "resume" in request.FILES:
            application.resume = request.FILES["resume"]

        application.save()

        logger.info(
            "RecommendCandidateAPI: %s recommended %s %s for '%s' | app_id=%s",
            user_display(request.user),
            applicant.first_name,
            applicant.last_name,
            application.role_applied_for,
            application.pk,
        )

        # --- Notify HR managers ---
        branch_label = branch.name if branch else "a branch"
        notify_many(
            recipients = _hr_managers(excluding=request.user),
            verb       = "recommendation_submitted",
            message    = (
                f"{user_display(request.user)} recommended {applicant.first_name} {applicant.last_name} "
                f"for {application.role_applied_for} from {branch_label}."
            ),
            link  = f"/hr/api/applications/{application.pk}/",
            actor = request.user,
        )

        return Response({
            "success":        True,
            "application_id": application.pk,
            "applicant":      f"{applicant.first_name} {applicant.last_name}",
            "role":           application.role_applied_for,
            "branch":         branch.name if branch else "—",
            "recommended_by": user_display(request.user),
        }, status=status.HTTP_201_CREATED)


class RecommendationListAPI(APIView):
    """Returns recommendations made by the current user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        applications = (
            RecruitmentApplication.objects
            .filter(source=RecruitmentSource.RECOMMENDATION, recommended_by=request.user)
            .select_related("applicant", "recommended_branch")
            .order_by("-created_at")
        )

        results = [
            {
                "id":         app.pk,
                "applicant":  str(app.applicant),
                "role":       app.role_applied_for,
                "branch":     app.recommended_branch.name if app.recommended_branch else "—",
                "stage":      app.current_stage,
                "status":     app.status,
                "priority":   app.priority,
                "created_at": app.created_at.strftime("%d %b %Y"),
            }
            for app in applications
        ]

        return Response(results)


class JobPositionListAPI(APIView):
    """Returns all active job positions for dropdowns."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from Human_Resources.models.job_position import JobPosition
        positions = (
            JobPosition.objects
            .filter(is_active=True)
            .select_related("department")
            .order_by("title")
        )
        return Response([
            {
                "id":         p.pk,
                "title":      p.title,
                "code":       p.code,
                "department": p.department.name if p.department else None,
            }
            for p in positions
        ])