# human_resources/models/recruitment_application.py

from django.db import models
from django.core.exceptions import ValidationError

from Human_Resources.constants import (
    ApplicationSource,
    ApplicationStatus,
)
from branches.models import Branch
from django.contrib.auth import get_user_model

User = get_user_model()


class RecruitmentApplication(models.Model):
    applicant = models.ForeignKey(
        "human_resources.Applicant",
        on_delete=models.CASCADE,
        related_name="applications"
    )

    source = models.CharField(
        max_length=20,
        choices=ApplicationSource.choices
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    recommended_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommended_applications"
    )

    role_applied_for = models.CharField(max_length=150)

    cv = models.FileField(
        upload_to="recruitment/cvs/",
        blank=True,
        null=True
    )

    remarks = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.SUBMITTED
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["source"]),
        ]

    def clean(self):
        """
        Enforce source-based integrity rules.
        """
        if self.source == ApplicationSource.MANAGER:
            if not self.branch or not self.recommended_by:
                raise ValidationError(
                    "Manager recommendations must have branch and recommended_by."
                )

        if self.source == ApplicationSource.PUBLIC:
            if self.branch or self.recommended_by:
                raise ValidationError(
                    "Public applications cannot have branch or recommended_by."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.applicant} → {self.role_applied_for}"
