# Human_Resources/api/views/branches.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from branches.models import Branch
from hr_workflows.models import RecruitmentApplication
from employees.models import Employee


class BranchListAPI(APIView):
    """
    Regional HR Branch Dashboard API

    Returns all branches strictly scoped to the logged-in HR user's region,
    including executive-level metrics required for branch cards.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        region_name = getattr(user, "region", None)

        if not region_name:
            return Response({
                "region": None,
                "count": 0,
                "branches": []
            })

        branches = (
            Branch.objects
            .filter(region__name=region_name)
            .order_by("name")
        )

        branch_data = []

        for branch in branches:
            total_employees = Employee.objects.filter(branch=branch).count()

            active_employees = Employee.objects.filter(
                branch=branch,
                is_active=True
            ).count()

            open_roles = RecruitmentApplication.objects.filter(
                recommended_branch=branch,
                current_stage__in=["submitted", "screening", "interview"]
            ).count()

            branch_data.append({
                "id": branch.id,
                "name": branch.name,
                "code": branch.code,
                "manager": branch.contact_person or "Unassigned",
                "active_since": branch.created_at.year if branch.created_at else None,
                "distance_from_hq": branch.distance_from_main_km,
                "total_employees": total_employees,
                "active_employees": active_employees,
                "open_roles": open_roles,
                "trend": None
            })

        return Response({
            "region": region_name,
            "count": len(branch_data),
            "branches": branch_data
        })
