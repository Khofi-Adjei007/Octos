# hr_workflows/models/onboarding_record.py

from django.db import models
from django.conf import settings
from django.utils import timezone


class OnboardingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    STALLED = "stalled", "Stalled"


class OnboardingRecord(models.Model):
    """
    Master onboarding record.
    Created automatically when application reaches hire_approved.
    One per hired application.
    """

    application = models.OneToOneField(
        "hr_workflows.RecruitmentApplication",
        on_delete=models.PROTECT,
        related_name="onboarding",
    )

    employee = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="onboarding_record",
    )

    current_phase = models.PositiveSmallIntegerField(default=1)

    status = models.CharField(
        max_length=20,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.PENDING,
        db_index=True,
    )

    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="initiated_onboardings",
    )

    # Time tracking
    initiated_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Notification tracking
    alert_sent_day_3 = models.BooleanField(default=False)
    alert_sent_day_5 = models.BooleanField(default=False)
    alert_sent_day_7 = models.BooleanField(default=False)

    class Meta:
        ordering = ["-initiated_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["current_phase"]),
            models.Index(fields=["initiated_at"]),
        ]

    @property
    def is_stalled(self):
        if self.status == OnboardingStatus.COMPLETED:
            return False
        days_pending = (timezone.now() - self.initiated_at).days
        return days_pending >= 7

    @property
    def days_since_initiated(self):
        return (timezone.now() - self.initiated_at).days

    def __str__(self):
        return f"Onboarding: {self.application} | Phase {self.current_phase} | {self.status}"