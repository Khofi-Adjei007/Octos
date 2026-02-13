from django.db import models
from django.contrib.auth import get_user_model
from Human_Resources.constants import RecruitmentStatus

User = get_user_model()



class RecruitmentEvaluation(models.Model):
    id = models.AutoField(primary_key=True)
    stage = models.CharField(max_length=50, choices=RecruitmentStatus.choices)
    career_score = models.FloatField(default=0.0)
    experience_score = models.FloatField(default=0.0)
    stability_score = models.FloatField(default=0.0)
    education_score = models.FloatField(default=0.0)
    skills_score = models.FloatField(default=0.0)
    weighted_score = models.FloatField(default=0.0)
    notes = models.TextField(blank=True, null=True)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recruitment_evaluations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_weighted_score(self):
        total_weighted_score = (
            self.career_score * 0.2 +
            self.experience_score * 0.3 +
            self.stability_score * 0.1 +
            self.education_score * 0.2 +
            self.skills_score * 0.2
        )
        self.weighted_score = round(total_weighted_score, 2)


        model = RecruitmentEvaluation
        fields = [
            "id",
            "stage",
            "career_score",
            "experience_score",
            "stability_score",
            "education_score",
            "skills_score",
            "weighted_score",
            "notes",
            "reviewer",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "weighted_score",
            "reviewer",
            "created_at",
            "updated_at",
        ]

    # -------------------------
    # FIELD VALIDATION
    # -------------------------

    def validate(self, data):

        score_fields = [
            "career_score",
            "experience_score",
            "stability_score",
            "education_score",
            "skills_score",
        ]

        for field in score_fields:
            value = data.get(field)

            if value is None:
                raise serializers.ValidationError(
                    f"{field} is required."
                )

            if value < 0 or value > 5:
                raise serializers.ValidationError(
                    f"{field} must be between 0 and 5."
                )

        if not data.get("notes") or not data["notes"].strip():
            raise serializers.ValidationError("Notes are required.")

        return data

    # -------------------------
    # CREATE
    # -------------------------

    def create(self, validated_data):
        validated_data["reviewer"] = self.context["request"].user

        instance = RecruitmentEvaluation.objects.create(**validated_data)

        instance.calculate_weighted_score()
        instance.save()

        return instance

    # -------------------------
    # UPDATE
    # -------------------------

    def update(self, instance, validated_data):

        for field in [
            "career_score",
            "experience_score",
            "stability_score",
            "education_score",
            "skills_score",
            "notes",
        ]:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.reviewer = self.context["request"].user

        instance.calculate_weighted_score()
        instance.save()

        return instance
