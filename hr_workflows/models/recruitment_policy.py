from django.db import models
from django.core.exceptions import ValidationError


class RecruitmentPolicy(models.Model):
    """
    Global recruitment workflow policy.

    Controls score thresholds and transition rules.
    Only ONE active policy is allowed at a time.
    """

    name = models.CharField(max_length=120, default="Default Global Policy")

    # ---------------------------
    # Stage Score Thresholds
    # ---------------------------

    screening_threshold = models.FloatField(default=4.0)
    interview_threshold = models.FloatField(default=5.0)
    final_review_threshold = models.FloatField(default=6.5)

    # ---------------------------
    # Control Flags (Future-proofing)
    # ---------------------------

    require_interview_date = models.BooleanField(default=True)
    require_finalized_evaluation = models.BooleanField(default=True)

    # ---------------------------
    # Activation
    # ---------------------------

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        """
        Enforce single active policy.
        """
        if self.is_active:
            qs = RecruitmentPolicy.objects.filter(is_active=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Only one active recruitment policy is allowed.")

    def __str__(self):
        return f"{self.name} (Active={self.is_active})"
