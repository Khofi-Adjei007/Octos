from rest_framework import serializers
from hr_workflows.models import RecruitmentEvaluation


class RecruitmentEvaluationSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecruitmentEvaluation
        fields = [
            "id",
            "stage",
            "data",
            "weighted_score",
            "reviewer",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "reviewer",
            "weighted_score",
            "created_at",
            "updated_at",
        ]

    # -------------------------
    # VALIDATION
    # -------------------------

    def validate_data(self, value):
        """
        Ensure required screening structure exists.
        Only enforce strict structure for screening stage.
        """

        stage = self.initial_data.get("stage")

        if stage == "screening":

            required_sections = [
                "career_path",
                "experience_depth",
                "job_stability",
                "education",
                "skills",
            ]

            for section in required_sections:
                if section not in value:
                    raise serializers.ValidationError(
                        f"{section} section is required."
                    )

                section_data = value.get(section)

                if "score" not in section_data:
                    raise serializers.ValidationError(
                        f"{section} must include a score."
                    )

                if "notes" not in section_data or not section_data["notes"].strip():
                    raise serializers.ValidationError(
                        f"{section} notes are required."
                    )

        return value

    # -------------------------
    # CREATE / UPDATE
    # -------------------------

    def create(self, validated_data):
        validated_data["reviewer"] = self.context["request"].user

        data = validated_data.get("data", {})
        stage = validated_data.get("stage")

        if stage == "screening":
            validated_data["weighted_score"] = self.calculate_weighted_score(data)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        data = validated_data.get("data", instance.data)
        stage = instance.stage

        if stage == "screening":
            instance.weighted_score = self.calculate_weighted_score(data)

        instance.data = data
        instance.save()
        return instance

    # -------------------------
    # WEIGHT CALCULATION
    # -------------------------

    def calculate_weighted_score(self, data):

        weights = {
            "experience_depth": 0.30,
            "skills": 0.30,
            "career_path": 0.20,
            "job_stability": 0.10,
            "education": 0.10,
        }

        total = 0

        for key, weight in weights.items():
            section = data.get(key, {})
            score = float(section.get("score", 0))
            total += score * weight

        return round(total, 2)
