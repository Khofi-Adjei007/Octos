from rest_framework import serializers
from employees.models import Employee


class EmployeeListSerializer(serializers.ModelSerializer):
    branch = serializers.StringRelatedField()
    role = serializers.StringRelatedField()
    department = serializers.StringRelatedField()

    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_id",
            "first_name",
            "last_name",
            "employee_email",
            "branch",
            "role",
            "employment_status",
        ]
