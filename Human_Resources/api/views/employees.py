# Human_Resources/api/views/employees.py

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from Human_Resources.services.query_scope import scoped_employee_queryset


class EmployeeListAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = scoped_employee_queryset(request.user)

        employees = []
        for e in queryset.select_related("branch", "role"):
            employees.append({
                "id":               e.pk,
                "first_name":       e.first_name,
                "last_name":        e.last_name,
                "position_title":   e.position_title or "",
                "employee_email":   e.employee_email or "",
                "branch":           e.branch.name if e.branch else None,
                "employment_status": e.employment_status or "",
                "is_active":        e.is_active,
                "approved":         e.approved_at is not None,
                "approved_at":      e.approved_at.isoformat() if e.approved_at else None,
                "role":             e.role.name if e.role else None,
            })

        return Response(employees)


class EmployeeApproveAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        queryset = scoped_employee_queryset(request.user)

        try:
            employee = queryset.get(pk=pk)
        except Exception:
            return Response(
                {"error": "Employee not found or not in your scope."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if employee.approved_at is not None:
            return Response(
                {"error": "Employee is already approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        employee.approved_at = timezone.now()
        employee.is_active = True
        employee.save(update_fields=["approved_at", "is_active"])

        return Response({
            "success": True,
            "employee_id": employee.pk,
            "approved_at": employee.approved_at.isoformat(),
        })