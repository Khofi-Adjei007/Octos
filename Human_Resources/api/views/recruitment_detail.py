from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.generics import get_object_or_404

from hr_workflows.models import RecruitmentApplication
from Human_Resources.services.query_scope import scoped_recruitment_queryset
from Human_Resources.api.serializers.recruitment_list import (
    RecruitmentListSerializer,
)


class RecruitmentDetailAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):

        queryset = scoped_recruitment_queryset(request.user)
        application = get_object_or_404(queryset, pk=pk)

        serializer = RecruitmentListSerializer(
            application,
            context={"request": request}
        )

        return Response(serializer.data)
