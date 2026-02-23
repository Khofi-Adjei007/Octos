from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from hr_workflows.models.recruitment_application import RecruitmentStage

User = get_user_model()


class RecruitmentEvaluation(models.Model):
    """
    Immutable stage-based evaluation model.

    Rules:
    - One reviewer per application per stage
    - Stage must match application's current stage
    - Cannot edit after finalization
    - Weighted score auto-calculated
    """

    application = models.ForeignKey(
        "hr_workflows.RecruitmentApplication",
        on_delete=models.CASCADE,
        related_name="evaluations",
        db_index=True,
    )

    stage = models.CharField(
        max_length=32,
        choices=RecruitmentStage.choices,
        db_index=True,
    )

    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recruitment_evaluations",
        db_index=True,
    )

    # ---------------------------
    # Scoring Dimensions
    # ---------------------------

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

    # ---------------------------
    # Finalization
    # ---------------------------

    is_finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(null=True, blank=True)

    finalized_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="finalized_recruitment_evaluations",
    )

    # ---------------------------
    # Timestamps
    # ---------------------------

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---------------------------
    # Meta
    # ---------------------------

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application", "stage"]),
            models.Index(fields=["reviewer"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["application", "stage", "reviewer"],
                name="unique_evaluation_per_stage_per_reviewer",
            )
        ]

    # ---------------------------
    # Validation
    # ---------------------------

    def clean(self):
        # Prevent editing finalized evaluations
        if self.pk:
            existing = RecruitmentEvaluation.objects.get(pk=self.pk)
            if existing.is_finalized:
                raise ValidationError("Cannot modify a finalized evaluation.")

        # Stage must match application current stage
        if self.stage != self.application.current_stage:
            raise ValidationError(
                "Evaluation stage must match application's current stage."
            )

    # ---------------------------
    # Score Calculation
    # ---------------------------

    def calculate_weighted_score(self):
        total = (
            self.career_score * 0.2
            + self.experience_score * 0.3
            + self.stability_score * 0.1
            + self.education_score * 0.2
            + self.skills_score * 0.2
        )
        self.weighted_score = round(total * 2, 2)

    # ---------------------------
    # Save Override
    # ---------------------------

    def save(self, *args, **kwargs):
        self.calculate_weighted_score()

        if self.is_finalized and not self.finalized_at:
            self.finalized_at = timezone.now()

        super().save(*args, **kwargs)

    # ---------------------------
    # String
    # ---------------------------

    def __str__(self):
        return f"{self.application} | {self.stage} | {self.reviewer}"
