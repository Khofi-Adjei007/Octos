from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from employees.models import Employee
from branches.models import Branch
from hr_workflows.models import RecruitmentApplication


class HROverviewAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # ---------------------------
        # REGION-SCOPED HR MANAGER
        # ---------------------------
        if user.region:

            branches = Branch.objects.filter(region__name=user.region)

            employees = Employee.objects.filter(
                branch__region__name=user.region
            )

            applications = RecruitmentApplication.objects.filter(
                recommended_branch__region__name=user.region
            )

            data = {
                "region_name": user.region,

                "branch_count": branches.count(),

                "total_employees": employees.count(),
                "active_employees": employees.filter(employment_status="ACTIVE").count(),
                "total_employees": employees.count(),
                "inactive_employees": employees.filter(employment_status="INACTIVE").count(),


                "critical": [],

                "total_applications": applications.count(),
                "pending": applications.filter(status="PENDING").count(),
                "approved": applications.filter(status="APPROVED").count(),
                "rejected": applications.filter(status="REJECTED").count(),
            }

            return Response(data)

        # ---------------------------
        # Fallback (non-regional users)
        # ---------------------------
        return Response({
            "region_name": "—",
            "branch_count": 0,
            "total_employees": 0,
            "critical": [],
            "total_applications": 0,
            "pending": 0,
            "approved": 0,
            "rejected": 0,
        })
