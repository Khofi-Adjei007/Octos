from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from Human_Resources.services.query_scope import (
    scoped_employee_queryset,
    scoped_recruitment_queryset,
)


class HROverviewAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        employees = scoped_employee_queryset(request.user)
        applications = scoped_recruitment_queryset(request.user)

        data = {
            "region_name": getattr(request.user.branch.region, "name", "—")
            if hasattr(request.user, "branch") and request.user.branch
            else "—",

            "branch_count": employees.values("branch").distinct().count(),

            "total_employees": employees.count(),

            "critical": [],

            "total_applications": applications.count(),
            "pending": applications.filter(status="PENDING").count(),
            "approved": applications.filter(status="APPROVED").count(),
            "rejected": applications.filter(status="REJECTED").count(),
        }

        return Response(data)
