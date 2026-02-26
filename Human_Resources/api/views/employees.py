# Human_Resources/api/views/employees.py

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from Human_Resources.services.query_scope import scoped_employee_queryset
from Human_Resources.models import AuthorityRole
from Human_Resources.models.authority import AuthorityAssignment
from branches.models import Branch, Region


class EmployeeListAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = scoped_employee_queryset(request.user)

        employees = []
        for e in queryset.select_related("branch", "role"):
            # Get current AuthorityAssignment
            assignment = (
                AuthorityAssignment.objects
                .filter(user=e, is_active=True)
                .select_related("role", "branch")
                .first()
            )
            employees.append({
                "id":                e.pk,
                "first_name":        e.first_name,
                "last_name":         e.last_name,
                "position_title":    e.position_title or "",
                "employee_email":    e.employee_email or "",
                "branch":            e.branch.name if e.branch else None,
                "employment_status": e.employment_status or "",
                "is_active":         e.is_active,
                "approved":          e.approved_at is not None,
                "approved_at":       e.approved_at.isoformat() if e.approved_at else None,
                "role":              e.role.name if e.role else None,
                "authority_role":    assignment.role.name if assignment and assignment.role else None,
                "authority_role_code": assignment.role.code if assignment and assignment.role else None,
                "has_assignment":    assignment is not None,
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


class EmployeeRoleOptionsAPI(APIView):
    """Returns available AuthorityRoles and Branches for the assignment modal."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        roles = [
            {"id": r.pk, "code": r.code, "name": r.name, "allowed_scopes": r.allowed_scopes}
            for r in AuthorityRole.objects.all().order_by("name")
        ]
        branches = [
            {"id": b.pk, "name": b.name}
            for b in Branch.objects.filter(is_active=True).order_by("name")
        ]
        regions = [
            {"id": r.pk, "name": r.name}
            for r in Region.objects.all().order_by("name")
        ]
        return Response({"roles": roles, "branches": branches, "regions": regions})


class EmployeeAssignRoleAPI(APIView):
    """Creates or updates AuthorityAssignment for an employee."""
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

        role_id    = request.data.get("role_id")
        scope_type = request.data.get("scope_type")
        branch_id  = request.data.get("branch_id")
        region_id  = request.data.get("region_id")

        if not role_id or not scope_type:
            return Response(
                {"error": "role_id and scope_type are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            role = AuthorityRole.objects.get(pk=role_id)
        except AuthorityRole.DoesNotExist:
            return Response({"error": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate scope
        if scope_type not in (role.allowed_scopes or []):
            return Response(
                {"error": f"Role '{role.name}' does not allow scope '{scope_type}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Deactivate existing assignments
        AuthorityAssignment.objects.filter(user=employee, is_active=True).update(is_active=False)

        # Build new assignment
        assignment = AuthorityAssignment(
            user=employee,
            role=role,
            scope_type=scope_type,
            is_active=True,
        )

        if scope_type == "BRANCH" and branch_id:
            try:
                assignment.branch = Branch.objects.get(pk=branch_id)
            except Branch.DoesNotExist:
                return Response({"error": "Invalid branch."}, status=status.HTTP_400_BAD_REQUEST)

        elif scope_type == "REGION" and region_id:
            try:
                assignment.region = Region.objects.get(pk=region_id)
            except Region.DoesNotExist:
                return Response({"error": "Invalid region."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assignment.full_clean()
            assignment.save()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "success": True,
            "employee_id": employee.pk,
            "role": role.name,
            "role_code": role.code,
            "scope_type": scope_type,
        })