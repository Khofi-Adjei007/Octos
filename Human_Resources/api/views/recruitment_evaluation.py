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

    # -------------------------
    # GET EVALUATION
    # -------------------------

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

    # -------------------------
    # CREATE / UPDATE
    # -------------------------

    def post(self, request, pk):

        queryset = scoped_recruitment_queryset(request.user)
        application = get_object_or_404(queryset, pk=pk)

        stage = request.data.get("stage")

        # Must match current stage
        if stage != application.current_stage:
            return Response(
                {"detail": "Evaluation must match current stage."},
                status=status.HTTP_400_BAD_REQUEST
            )

        evaluation = RecruitmentEvaluation.objects.filter(
            application=application,
            stage=stage
        ).first()

        # If evaluation exists but stage already changed, block editing
        if evaluation and application.current_stage != stage:
            return Response(
                {"detail": "Cannot edit evaluation after stage transition."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RecruitmentEvaluationSerializer(
            evaluation,
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            saved = serializer.save(
                application=application,
                reviewer=request.user,
                stage=stage
            )
            return Response(
                RecruitmentEvaluationSerializer(saved).data,
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
