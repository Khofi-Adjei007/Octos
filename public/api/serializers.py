# public/api/serializers.py
from rest_framework import serializers
from Human_Resources.models import PublicApplication, Role

class PublicApplicationSerializer(serializers.ModelSerializer):
    recommended_role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), required=False, allow_null=True
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
