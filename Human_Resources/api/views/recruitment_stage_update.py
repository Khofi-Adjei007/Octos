from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.generics import get_object_or_404

from django.utils import timezone

from hr_workflows.models import RecruitmentApplication, RecruitmentEvaluation
from Human_Resources.services.query_scope import scoped_recruitment_queryset
from Human_Resources.constants import RecruitmentStatus
from Human_Resources.api.serializers.recruitment_detail import RecruitmentDetailSerializer


STAGE_ORDER = [
    RecruitmentStatus.SUBMITTED,
    RecruitmentStatus.SCREENING,
    RecruitmentStatus.INTERVIEW,
    RecruitmentStatus.FINAL_REVIEW,
    RecruitmentStatus.OFFER,
    RecruitmentStatus.ONBOARDED,
]


class RecruitmentStageUpdateAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):

        queryset = scoped_recruitment_queryset(request.user)
        application = get_object_or_404(queryset, pk=pk)

        new_stage = request.data.get("stage")

        if not new_stage:
            return Response(
                {"detail": "Stage is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # -----------------------------------
        # TERMINAL PROTECTION
        # -----------------------------------

        if application.status in {
            RecruitmentStatus.ONBOARDED,
            RecruitmentStatus.REJECTED,
        }:
            return Response(
                {"detail": "Application is already closed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # -----------------------------------
        # REJECT ALWAYS ALLOWED
        # -----------------------------------

        if new_stage == RecruitmentStatus.REJECTED:
            application.status = RecruitmentStatus.REJECTED
            application.current_stage = RecruitmentStatus.REJECTED
            application.stage_updated_at = timezone.now()
            application.closed_at = timezone.now()
            application.save()

            serializer = RecruitmentDetailSerializer(
                application,
                context={"request": request}
            )
            return Response(serializer.data)

        # -----------------------------------
        # ENFORCE FORWARD-ONLY PROGRESSION
        # -----------------------------------

        try:
            current_index = STAGE_ORDER.index(application.current_stage)
            next_stage = STAGE_ORDER[current_index + 1]
        except (ValueError, IndexError):
            return Response(
                {"detail": "Invalid stage transition."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_stage != next_stage:
            return Response(
                {"detail": "Only forward progression allowed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # -----------------------------------
        # SCREENING → INTERVIEW CHECKS
        # -----------------------------------

        if (
            application.current_stage == RecruitmentStatus.SCREENING
            and new_stage == RecruitmentStatus.INTERVIEW
        ):

            evaluation = RecruitmentEvaluation.objects.filter(
                application=application,
                stage=RecruitmentStatus.SCREENING
            ).first()

            if not evaluation:
                return Response(
                    {"detail": "Screening evaluation required before proceeding."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not evaluation.is_finalized:
                return Response(
                    {"detail": "Screening must be finalized before proceeding."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if evaluation.weighted_score is None:
                return Response(
                    {"detail": "Screening score not available."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if float(evaluation.weighted_score) < 4:
                return Response(
                    {
                        "detail": "Candidate below screening threshold (minimum 4.0 required)."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        # -----------------------------------
        # APPLY STAGE TRANSITION
        # -----------------------------------

        application.current_stage = new_stage
        application.status = new_stage
        application.stage_updated_at = timezone.now()

        if new_stage == RecruitmentStatus.ONBOARDED:
            application.closed_at = timezone.now()

        application.save()

        serializer = RecruitmentDetailSerializer(
            application,
            context={"request": request}
        )

        return Response(serializer.data)
