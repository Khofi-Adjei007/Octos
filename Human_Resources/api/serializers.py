# Human_Resources/api/serializers.py
from rest_framework import serializers
from employees.models import Employee
from Human_Resources.models import PublicApplication

class EmployeeCreateFromApplicationSerializer(serializers.Serializer):
    application_id = serializers.IntegerField()
    employee_email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True, required=False)

    def validate(self, attrs):
        app_id = attrs.get('application_id')
        try:
            self.application = PublicApplication.objects.get(pk=app_id)
        except PublicApplication.DoesNotExist:
            raise serializers.ValidationError("Application not found.")
        if self.application.status not in ['pending', 'shortlisted', 'approved']:
            raise serializers.ValidationError("Application is not eligible for conversion.")
        return attrs

    def create(self, validated_data):
        # minimal mapping — adapt as required
        app = self.application
        email = validated_data.get('employee_email') or app.email
        password = validated_data.get('password') or Employee.objects.make_random_password()
        emp = Employee.objects.create_user(
            employee_email=email,
            password=password,
            first_name=app.first_name,
            last_name=app.last_name,
            phone_number=app.phone or "",
            date_of_birth=None,  # you may request later
            address="",
            is_active=True
        )
        # mark application as hired/linked
        app.status = "hired"
        app.employee = emp
        app.save(update_fields=["status", "employee"])
        return emp
