# hr_workflows/models/recruitment_evaluation.py

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

    stage = models.CharField(
        max_length=20,
        choices=RecruitmentStatus.choices
    )

    score = models.DecimalField(
        max_digits=3,
        decimal_places=1
    )

    notes = models.TextField()

    reviewer = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("application", "stage")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.application} - {self.stage} ({self.score})"
