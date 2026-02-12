from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from Human_Resources.services.query_scope import scoped_recruitment_queryset
from Human_Resources.api.serializers.recruitment_list import (
    RecruitmentListSerializer,
)


class RecruitmentListAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = scoped_recruitment_queryset(request.user)

        status_param = request.query_params.get("status")

        if status_param:
            queryset = queryset.filter(status=status_param)

        serializer = RecruitmentListSerializer(queryset, many=True, context={"request": request})
        
        return Response(serializer.data)
