# Human_Resources/api/views/interviewers.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from employees.models import Employee

INTERVIEWER_ROLE_CODES = [
    'BELT_HR_OVERSEER',
    'BRANCH_MANAGER',
    'HR_ADMIN',
    'SUPER_ADMIN',
]

class InterviewerListAPI(APIView):
    """
    Returns employees eligible to conduct interviews.
    Filtered by authority role codes.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        interviewers = Employee.objects.filter(
            is_active=True,
            authority_roles__code__in=INTERVIEWER_ROLE_CODES,
        ).distinct().values('id', 'first_name', 'last_name', 'employee_email')

        data = [
            {
                "id": e['id'],
                "name": f"{e['first_name']} {e['last_name']}",
                "email": e['employee_email'],
            }
            for e in interviewers
        ]

        return Response(data)