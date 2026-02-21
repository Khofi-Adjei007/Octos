from rest_framework import serializers
from hr_workflows.models import RecruitmentEvaluation


class RecruitmentEvaluationSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecruitmentEvaluation
        fields = "__all__"
        read_only_fields = [
            "application",
            "reviewer",
            "stage",
            "weighted_score",
            "created_at",
            "updated_at",
            "is_finalized",
            "finalized_at",
            "finalized_by",
        ]

    def create(self, validated_data):
        validated_data["reviewer"] = self.context["request"].user
        instance = super().create(validated_data)
        instance.calculate_weighted_score()
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.calculate_weighted_score()
        instance.save()
        return instance