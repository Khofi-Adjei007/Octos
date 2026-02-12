from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.generics import get_object_or_404

from hr_workflows.models import RecruitmentApplication, RecruitmentEvaluation
from Human_Resources.services.query_scope import scoped_recruitment_queryset
from Human_Resources.api.serializers.recruitment_evaluation import (
    RecruitmentEvaluationSerializer,
)


class RecruitmentEvaluationAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):

        queryset = scoped_recruitment_queryset(request.user)
        application = get_object_or_404(queryset, pk=pk)

        evaluation = RecruitmentEvaluation.objects.filter(
            application=application,
            stage=application.current_stage
        ).first()

        if not evaluation:
            return Response({}, status=status.HTTP_200_OK)

        serializer = RecruitmentEvaluationSerializer(evaluation)
        return Response(serializer.data)

    def post(self, request, pk):

        queryset = scoped_recruitment_queryset(request.user)
        application = get_object_or_404(queryset, pk=pk)

        stage = request.data.get("stage")

        if stage != application.current_stage:
            return Response(
                {"detail": "Evaluation must match current stage."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prevent editing if stage already moved
        existing = RecruitmentEvaluation.objects.filter(
            application=application,
            stage=stage
        ).first()

        if existing and application.current_stage != stage:
            return Response(
                {"detail": "Cannot edit evaluation after stage transition."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RecruitmentEvaluationSerializer(
            existing,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            evaluation = serializer.save(
                application=application,
                reviewer=request.user,
                stage=stage
            )
            return Response(
                RecruitmentEvaluationSerializer(evaluation).data
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
