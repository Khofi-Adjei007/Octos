# human_resources/models/recruitment_application.py

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from Human_Resources.constants import RecruitmentStatus, RecruitmentSource
from branches.models import Branch

User = get_user_model()


class RecruitmentApplication(models.Model):
    applicant = models.ForeignKey(
        "hr_workflows.Applicant",
        on_delete=models.CASCADE,
        related_name="applications"
    )

    # how the person entered the pipeline
    source = models.CharField(
        max_length=20,
        choices=RecruitmentSource.choices
    )

    # recommendation context (optional, but accountable)
    recommended_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recruitment_recommendations"
    )

    recommended_branch = models.ForeignKey(
        Branch,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    role_applied_for = models.CharField(max_length=150)
    resume = models.FileField(upload_to="recruitment/resumes/", null=True, blank=True, help_text="Uploaded CV / Resume document")
    status = models.CharField(
        max_length=20,
        choices=RecruitmentStatus.choices,
        default=RecruitmentStatus.SUBMITTED
    )

    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["source"]),
        ]

    def clean(self):
        # recommendation integrity
        if self.source == RecruitmentSource.RECOMMENDATION:
            if not self.recommended_by:
                raise ValidationError("Recommendation must have a recommender.")

        if self.source == RecruitmentSource.PUBLIC:
            if self.recommended_by or self.recommended_branch:
                raise ValidationError("Public applications cannot have recommendation data.")

    def is_terminal(self):
        return self.status in {
            RecruitmentStatus.ONBOARDED,
            RecruitmentStatus.REJECTED,
        }

    def __str__(self):
        return f"{self.applicant} → {self.role_applied_for}"
