# Human_Resources/api/views/onboarding.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.generics import get_object_or_404

from hr_workflows.models import RecruitmentApplication
from hr_workflows.models.onboarding_record import OnboardingRecord
from hr_workflows.onboarding_engine import OnboardingEngine, OnboardingError
from Human_Resources.services.query_scope import scoped_recruitment_queryset


class OnboardingInitiateAPI(APIView):
    """
    Called when HR clicks 'Start Onboarding' from the celebratory modal.
    pk = application pk.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        queryset = scoped_recruitment_queryset(request.user)
        application = get_object_or_404(queryset, pk=pk)

        if application.status != "hire_approved":
            return Response(
                {"detail": "Onboarding can only be initiated for hired applicants."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record = OnboardingEngine.initiate(
            application=application,
            initiated_by=request.user,
        )

        return Response({
            "onboarding_id": record.pk,
            "current_phase": record.current_phase,
            "status": record.status,
            "applicant": str(application.applicant),
            "role": application.role_applied_for,
            "message": "Onboarding record is ready.",
        }, status=status.HTTP_200_OK)


class OnboardingPhaseOneAPI(APIView):
    """
    HR completes Phase 1 — personal information and setup.
    pk = onboarding record pk.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        record = get_object_or_404(OnboardingRecord, pk=pk)

        try:
            OnboardingEngine.complete_phase_one(
                record=record,
                actor=request.user,
                data=request.data,
            )
        except OnboardingError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record.refresh_from_db()

        return Response({
            "onboarding_id": record.pk,
            "current_phase": record.current_phase,
            "status": record.status,
            "message": "Phase 1 completed. Proceed to documentation.",
        }, status=status.HTTP_200_OK)


class OnboardingPhaseTwoAPI(APIView):
    """
    HR completes Phase 2 — documentation.
    Handles file uploads and guarantor details for cashiers.
    pk = onboarding record pk.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        record = get_object_or_404(OnboardingRecord, pk=pk)

        try:
            OnboardingEngine.complete_phase_two(
                record=record,
                actor=request.user,
                data=request.data,
                files=request.FILES,
            )
        except OnboardingError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record.refresh_from_db()

        return Response({
            "onboarding_id": record.pk,
            "current_phase": record.current_phase,
            "status": record.status,
            "message": "Phase 2 completed. Awaiting branch confirmation.",
        }, status=status.HTTP_200_OK)


class OnboardingPhaseThreeAPI(APIView):
    """
    Branch manager confirms employee has physically reported.
    Activates employee account on completion.
    pk = onboarding record pk.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        record = get_object_or_404(OnboardingRecord, pk=pk)

        try:
            OnboardingEngine.complete_phase_three(
                record=record,
                actor=request.user,
            )
        except OnboardingError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record.refresh_from_db()

        return Response({
            "onboarding_id": record.pk,
            "current_phase": record.current_phase,
            "status": record.status,
            "message": "Onboarding complete. Employee is now fully active.",
        }, status=status.HTTP_200_OK)


class OnboardingStatusAPI(APIView):
    """
    Returns current onboarding status.
    pk = application pk — looks up onboarding record via application.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        # Look up by application pk not onboarding record pk
        record = get_object_or_404(OnboardingRecord, application__pk=pk)

        phases = record.phases.all().order_by("phase_number")
        phase_data = [
            {
                "phase_number": p.phase_number,
                "status": p.status,
                "completed_at": p.completed_at,
                "completed_by": str(p.completed_by) if p.completed_by else None,
            }
            for p in phases
        ]

        return Response({
            "onboarding_id": record.pk,
            "applicant": str(record.application.applicant),
            "role": record.application.role_applied_for,
            "current_phase": record.current_phase,
            "status": record.status,
            "days_since_initiated": record.days_since_initiated,
            "is_stalled": record.is_stalled,
            "started_at": record.started_at,
            "completed_at": record.completed_at,
            "phases": phase_data,
        }, status=status.HTTP_200_OK)