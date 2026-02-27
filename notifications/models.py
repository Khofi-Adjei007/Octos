from django.db import models
from django.conf import settings


class NotificationVerb(models.TextChoices):
    RECOMMENDATION_SUBMITTED = "recommendation_submitted", "Recommendation Submitted"
    STAGE_CHANGED            = "stage_changed",            "Stage Changed"
    OFFER_EXTENDED           = "offer_extended",           "Offer Extended"
    EMPLOYEE_APPROVED        = "employee_approved",        "Employee Approved"
    ONBOARDING_COMPLETED     = "onboarding_completed",     "Onboarding Completed"


class Notification(models.Model):
    """
    Generic notification record.

    Usage:
        from notifications.services import notify
        notify(recipient=user, verb="stage_changed", message="...", link="/hr/...")
    """

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_notifications",
    )

    verb = models.CharField(
        max_length=64,
        choices=NotificationVerb.choices,
        db_index=True,
    )

    message = models.CharField(max_length=512)

    link = models.CharField(
        max_length=512,
        blank=True,
        default="",
        help_text="Relative URL to navigate to on click",
    )

    is_read = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes  = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["recipient", "created_at"]),
        ]

    def __str__(self):
        return f"→ {self.recipient} | {self.verb} | {'read' if self.is_read else 'unread'}"