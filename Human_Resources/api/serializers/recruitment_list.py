from rest_framework import serializers
from hr_workflows.models import RecruitmentApplication


class RecruitmentListSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="applicant.first_name")
    last_name = serializers.CharField(source="applicant.last_name")
    email = serializers.CharField(source="applicant.email", allow_null=True)
    recommended_role = serializers.CharField(source="role_applied_for")
    status = serializers.SerializerMethodField()

    class Meta:
        model = RecruitmentApplication
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "recommended_role",
            "status",
        ]

    def get_status(self, obj):
        return obj.status.lower()
