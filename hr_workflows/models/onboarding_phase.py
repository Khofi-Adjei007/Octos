# hr_workflows/models/onboarding_phase.py

from django.db import models
from django.conf import settings


class PhaseStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"


class OnboardingPhase(models.Model):
    """
    Tracks each phase of the onboarding process.
    Phase 1 — Setup (HR)
    Phase 2 — Documentation (HR)
    Phase 3 — Reporting Confirmation (Branch Manager)
    """

    onboarding = models.ForeignKey(
        "hr_workflows.OnboardingRecord",
        on_delete=models.CASCADE,
        related_name="phases",
    )

    phase_number = models.PositiveSmallIntegerField()

    status = models.CharField(
        max_length=20,
        choices=PhaseStatus.choices,
        default=PhaseStatus.PENDING,
        db_index=True,
    )

    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_onboarding_phases",
    )

    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    # -----------------------------------------------
    # Phase 1 fields — Setup
    # -----------------------------------------------
    house_number = models.CharField(max_length=100, blank=True)
    nearest_landmark = models.CharField(max_length=255, blank=True)
    ghana_card_number = models.CharField(max_length=50, blank=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)

    # -----------------------------------------------
    # Phase 2 fields — Documentation
    # -----------------------------------------------
    contract_signed = models.BooleanField(default=False)
    contract_signed_date = models.DateField(null=True, blank=True)
    contract_upload = models.FileField(
        upload_to="onboarding/contracts/",
        null=True,
        blank=True,
    )
    ghana_card_upload = models.FileField(
        upload_to="onboarding/ghana_cards/",
        null=True,
        blank=True,
    )
    ghana_card_verification_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("verified", "Verified"),
            ("failed", "Failed"),
        ],
        default="pending",
    )
    bank_name = models.CharField(max_length=120, blank=True)
    bank_account_number = models.CharField(max_length=64, blank=True)
    ssnit_number = models.CharField(max_length=64, blank=True)
    tin_number = models.CharField(max_length=64, blank=True)

    # -----------------------------------------------
    # Phase 3 fields — Reporting Confirmation
    # -----------------------------------------------
    reported_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="branch_confirmations",
    )

    class Meta:
        ordering = ["phase_number"]
        unique_together = ["onboarding", "phase_number"]

    def __str__(self):
        return f"Phase {self.phase_number} | {self.onboarding} | {self.status}"