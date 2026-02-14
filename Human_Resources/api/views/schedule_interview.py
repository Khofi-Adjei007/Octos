from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.generics import get_object_or_404

from django.db import transaction
from django.utils import timezone

from hr_workflows.models import (
    RecruitmentApplication,
    RecruitmentEvaluation,
)

from Human_Resources.services.query_scope import scoped_recruitment_queryset
from Human_Resources.constants import RecruitmentStatus
from Human_Resources.api.serializers.recruitment_detail import (
    RecruitmentDetailSerializer,
)


class ScheduleInterviewAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):

        queryset = scoped_recruitment_queryset(request.user)
        application = get_object_or_404(queryset, pk=pk)

        interview_date = request.data.get("interview_date")
        interviewer_name = request.data.get("interviewer")

        if not interview_date:
            return Response(
                {"detail": "Interview date is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not interviewer_name:
            return Response(
                {"detail": "Interviewer is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------------------------------
        # Must currently be in screening
        # ---------------------------------------

        if application.current_stage != RecruitmentStatus.SCREENING:
            return Response(
                {"detail": "Interview can only be scheduled from screening stage."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------------------------------
        # Screening evaluation checks
        # ---------------------------------------

        evaluation = RecruitmentEvaluation.objects.filter(
            application=application,
            stage=RecruitmentStatus.SCREENING
        ).first()

        if not evaluation:
            return Response(
                {"detail": "Screening evaluation required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not evaluation.is_finalized:
            return Response(
                {"detail": "Screening must be finalized before scheduling interview."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if evaluation.weighted_score is None:
            return Response(
                {"detail": "Screening score missing."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if float(evaluation.weighted_score) < 4:
            return Response(
                {"detail": "Candidate below screening threshold (minimum 4.0 required)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------------------------------
        # APPLY ATOMIC TRANSITION
        # ---------------------------------------

        application.interview_date = interview_date
        application.assigned_reviewer = None  # Optional: map interviewer to user later
        application.current_stage = RecruitmentStatus.INTERVIEW
        application.status = RecruitmentStatus.INTERVIEW
        application.stage_updated_at = timezone.now()

        application.save()

        serializer = RecruitmentDetailSerializer(
            application,
            context={"request": request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)
