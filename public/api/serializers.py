# public/api/serializers.py
from rest_framework import serializers
from hr_workflows.models import recruitment_legacy as rec_legacy
from hr_workflows.models.recruitment_legacy import PublicApplication

class PublicApplicationSerializer(serializers.ModelSerializer):
    recommended_role = serializers.PrimaryKeyRelatedField(
        queryset=rec_legacy.Role.objects.all(), required=False, allow_null=True
    )
    resume = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = PublicApplication
        fields = [
            "id", "first_name", "middle_name", "last_name",
            "email", "phone", "recommended_role", "resume", "notes",
            "status", "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]
