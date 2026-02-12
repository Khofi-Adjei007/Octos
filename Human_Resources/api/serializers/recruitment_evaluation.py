from rest_framework import serializers
from hr_workflows.models import RecruitmentEvaluation


class RecruitmentEvaluationSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecruitmentEvaluation
        fields = [
            "id",
            "stage",
            "score",
            "notes",
            "reviewer",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["reviewer", "created_at", "updated_at"]

    def validate_score(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError("Score must be between 0 and 10.")
        return value

    def validate_notes(self, value):
        if not value.strip():
            raise serializers.ValidationError("Notes are required.")
        return value
