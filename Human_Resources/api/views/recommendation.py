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


logger = logging.getLogger(__name__)


class RecommendCandidateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        data = request.data

        # Safe display name for any user model
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

        # Must have either position_id or role_applied_for
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
                return Response(
                    {"error": "Invalid branch."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # --- Resolve position FK ---
        position = None
        position_id = data.get("position_id")
        if position_id:
            try:
                position = JobPosition.objects.get(pk=position_id, is_active=True)
            except JobPosition.DoesNotExist:
                return Response(
                    {"error": "Invalid position selected."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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

        # Attach CV if uploaded
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
            .filter(
                source=RecruitmentSource.RECOMMENDATION,
                recommended_by=request.user,
            )
            .select_related("applicant", "recommended_branch")
            .order_by("-created_at")
        )

        results = []
        for app in applications:
            results.append({
                "id":           app.pk,
                "applicant":    str(app.applicant),
                "role":         app.role_applied_for,
                "branch":       app.recommended_branch.name if app.recommended_branch else "—",
                "stage":        app.current_stage,
                "status":       app.status,
                "priority":     app.priority,
                "created_at":   app.created_at.strftime("%d %b %Y"),
            })

        return Response(results)


class JobPositionListAPI(APIView):
    """Returns all active job positions for dropdowns."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
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