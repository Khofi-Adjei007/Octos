from django.db import models
from django.contrib.auth import get_user_model
from Human_Resources.constants import RecruitmentStatus

User = get_user_model()

class RecruitmentEvaluation(models.Model):

    application = models.ForeignKey(
        "hr_workflows.RecruitmentApplication",
        on_delete=models.CASCADE,
        related_name="evaluations"
    )

    stage = models.CharField(max_length=50, choices=RecruitmentStatus.choices)

    career_score = models.FloatField(default=0.0)
    career_notes = models.TextField(blank=True, null=True)

    experience_score = models.FloatField(default=0.0)
    experience_notes = models.TextField(blank=True, null=True)

    stability_score = models.FloatField(default=0.0)
    stability_notes = models.TextField(blank=True, null=True)

    education_score = models.FloatField(default=0.0)
    education_notes = models.TextField(blank=True, null=True)

    skills_score = models.FloatField(default=0.0)
    skills_notes = models.TextField(blank=True, null=True)

    weighted_score = models.FloatField(default=0.0)
    is_finalized = models.BooleanField(default=False)

    finalized_at = models.DateTimeField(null=True, blank=True)

    finalized_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="finalized_recruitment_evaluations")

    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recruitment_evaluations"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_weighted_score(self):
        total = (
            self.career_score * 0.2 +
            self.experience_score * 0.3 +
            self.stability_score * 0.1 +
            self.education_score * 0.2 +
            self.skills_score * 0.2
        )
        self.weighted_score = round(total, 2)

    def __str__(self):
        return f"{self.application} - {self.stage}"

