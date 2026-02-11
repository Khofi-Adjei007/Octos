from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from Human_Resources.services.query_scope import scoped_employee_queryset
from Human_Resources.api.serializers.employee_list import EmployeeListSerializer


class EmployeeListAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = scoped_employee_queryset(request.user)

        serializer = EmployeeListSerializer(queryset, many=True)

        return Response(serializer.data)
