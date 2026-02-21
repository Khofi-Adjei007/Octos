from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

from hr_workflows.models import RecruitmentApplication

User = get_user_model()


class RecruitmentTransitionLog(models.Model):
    """
    Immutable audit trail for recruitment transitions.
    """

    application = models.ForeignKey(
        RecruitmentApplication,
        on_delete=models.CASCADE,
        related_name="transition_logs",
    )

    action = models.CharField(max_length=50)

    performed_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="recruitment_transitions",
    )

    previous_stage = models.CharField(max_length=32)
    new_stage = models.CharField(max_length=32)

    previous_status = models.CharField(max_length=32)
    new_status = models.CharField(max_length=32)

    payload_snapshot = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.application} | {self.action} | {self.created_at}"