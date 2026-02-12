# human_resources/models/recruitment_application.py

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from Human_Resources.constants import RecruitmentStatus, RecruitmentSource
from branches.models import Branch

User = get_user_model()


class RecruitmentStage(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    SCREENING = "screening", "Screening"
    INTERVIEW = "interview", "Interview"
    FINAL_REVIEW = "final_review", "Final Review"
    OFFER = "offer", "Offer"
    COMPLETED = "completed", "Completed"  # aligns with onboarding


class RecruitmentApplication(models.Model):

    applicant = models.ForeignKey(
        "hr_workflows.Applicant",
        on_delete=models.CASCADE,
        related_name="applications"
    )

    source = models.CharField(
        max_length=20,
        choices=RecruitmentSource.choices
    )

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

    resume = models.FileField(
        upload_to="recruitment/resumes/",
        null=True,
        blank=True,
        help_text="Uploaded CV / Resume document"
    )

    # Terminal decision
    status = models.CharField(
        max_length=20,
        choices=RecruitmentStatus.choices,
        default=RecruitmentStatus.SUBMITTED
    )

    # Workflow stage (NEW)
    current_stage = models.CharField(
        max_length=30,
        choices=RecruitmentStage.choices,
        default=RecruitmentStage.SUBMITTED
    )

    # Ownership
    assigned_reviewer = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_recruitment_reviews"
    )

    # Interview scheduling
    interview_date = models.DateTimeField(null=True, blank=True)

    # Priority support
    priority = models.CharField(
        max_length=20,
        default="normal"
    )

    # Tracking
    stage_updated_at = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["source"]),
            models.Index(fields=["current_stage"]),
            models.Index(fields=["priority"]),
        ]

    def clean(self):
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

    @property
    def is_new(self):
        return (
            self.status == RecruitmentStatus.SUBMITTED and
            timezone.now() - self.created_at <= timezone.timedelta(hours=24)
        )

    def __str__(self):
        return f"{self.applicant} → {self.role_applied_for}"
