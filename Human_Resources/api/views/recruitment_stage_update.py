from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.generics import get_object_or_404

from Human_Resources.services.query_scope import scoped_recruitment_queryset
from Human_Resources.api.serializers.recruitment_detail import RecruitmentDetailSerializer
from Human_Resources.recruitment_services.transitions import RecruitmentEngine
from Human_Resources.recruitment_services.exceptions import InvalidTransition


class RecruitmentStageUpdateAPI(APIView):
    """
    Unified endpoint for stage progression and final decision.

    All logic delegated to RecruitmentEngine.
    """

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):

        queryset = scoped_recruitment_queryset(request.user)
        application = get_object_or_404(queryset, pk=pk)

        target = request.data.get("stage")

        if not target:
            return Response(
                {"detail": "Stage is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # -----------------------------------
            # Decision handling
            # -----------------------------------
            if target in {"offer", "rejected"}:
                RecruitmentEngine.make_decision(application, target)

            # -----------------------------------
            # Stage movement
            # -----------------------------------
            else:
                RecruitmentEngine.move_to_stage(
                    application=application,
                    next_stage=target,
                    actor=request.user
                )

        except InvalidTransition as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RecruitmentDetailSerializer(
            application,
            context={"request": request}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)