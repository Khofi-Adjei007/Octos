# hr_workflows/models/recruitment_application.py

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from Human_Resources.constants import RecruitmentSource
from branches.models import Branch

User = get_user_model()


# =========================================================
# WORKFLOW STAGES (PROCESS FLOW ONLY)
# =========================================================

class RecruitmentStage(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    SCREENING = "screening", "Screening"
    INTERVIEW = "interview", "Interview"
    FINAL_REVIEW = "final_review", "Final Review"
    DECISION = "decision", "Decision"


# =========================================================
# TERMINAL / DECISION STATES (OUTCOME ONLY)
# =========================================================

class RecruitmentDecision(models.TextChoices):
    ACTIVE = "active", "Active"
    REJECTED = "rejected", "Rejected"
    OFFER_EXTENDED = "offer_extended", "Offer Extended"
    HIRE_APPROVED = "hire_approved", "Hire Approved"
    WITHDRAWN = "withdrawn", "Withdrawn"
    CLOSED = "closed", "Closed"


# =========================================================
# MAIN MODEL
# =========================================================

class RecruitmentApplication(models.Model):
    """
    Canonical recruitment record.

    Stage = workflow progress.
    Status = decision outcome.

    Onboarding is handled by a separate engine.
    """

    # -----------------------------------------------------
    # Core Relations
    # -----------------------------------------------------

    applicant = models.ForeignKey(
        "hr_workflows.Applicant",
        on_delete=models.CASCADE,
        related_name="applications",
    )

    source = models.CharField(
        max_length=20,
        choices=RecruitmentSource.choices,
        db_index=True,
    )

    recommended_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recruitment_recommendations",
    )

    recommended_branch = models.ForeignKey(
        Branch,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recommended_applications",
    )

    role_applied_for = models.CharField(
        max_length=150,
        db_index=True,
    )

    resume = models.FileField(
        upload_to="recruitment/resumes/",
        null=True,
        blank=True,
        help_text="Uploaded CV / Resume document",
    )

    # -----------------------------------------------------
    # Workflow
    # -----------------------------------------------------

    current_stage = models.CharField(
        max_length=32,
        choices=RecruitmentStage.choices,
        default=RecruitmentStage.SUBMITTED,
        db_index=True,
    )

    status = models.CharField(
        max_length=32,
        choices=RecruitmentDecision.choices,
        default=RecruitmentDecision.ACTIVE,
        db_index=True,
    )

    assigned_reviewer = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_recruitment_reviews",
    )

    interview_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    priority = models.CharField(
        max_length=20,
        default="normal",
        db_index=True,
    )

    # -----------------------------------------------------
    # Tracking
    # -----------------------------------------------------

    stage_updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # -----------------------------------------------------
    # Meta
    # -----------------------------------------------------

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["current_stage"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["source"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["recommended_branch"]),
        ]

    # =====================================================
    # VALIDATION
    # =====================================================

    def clean(self):
        """
        Enforces business invariants.
        Does NOT enforce stage transitions here.
        """

        # Recommendation rules
        if self.source == RecruitmentSource.RECOMMENDATION:
            if not self.recommended_by:
                raise ValidationError("Recommendation must have a recommender.")

            if not self.recommended_branch:
                raise ValidationError("Recommended applications must specify a branch.")

        if self.source == RecruitmentSource.PUBLIC:
            if self.recommended_by or self.recommended_branch:
                raise ValidationError(
                    "Public applications cannot contain recommendation metadata."
                )

        # Terminal status must only occur at decision stage
        if self.status != RecruitmentDecision.ACTIVE:
            if self.current_stage != RecruitmentStage.DECISION:
                raise ValidationError(
                    "Non-active decisions may only be set at Decision stage."
                )

    # =====================================================
    # STATE HELPERS
    # =====================================================

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            RecruitmentDecision.REJECTED,
            RecruitmentDecision.HIRE_APPROVED,
            RecruitmentDecision.WITHDRAWN,
            RecruitmentDecision.CLOSED,
        }

    @property
    def is_active(self) -> bool:
        return self.status == RecruitmentDecision.ACTIVE

    @property
    def is_new(self) -> bool:
        return (
            self.current_stage == RecruitmentStage.SUBMITTED
            and timezone.now() - self.created_at <= timezone.timedelta(hours=24)
        )

    # =====================================================
    # REPRESENTATION
    # =====================================================

    def __str__(self):
        return f"{self.applicant} → {self.role_applied_for}"
