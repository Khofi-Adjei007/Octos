# Human_Resources/models/job_position.py

from django.db import models
from django.utils.text import slugify


class JobPosition(models.Model):
    """
    Global master list of job positions at Farhat Printing Press.
    Used in recruitment, recommendations, and employee profiles.
    Not scoped per branch — positions are company-wide.
    """

    title = models.CharField(
        max_length=150,
        unique=True,
        help_text="e.g. General Attendant, Branch Manager",
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Short unique code e.g. GEN_ATT, BR_MGR",
    )
    department = models.ForeignKey(
        "Human_Resources.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="positions",
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Brief description of the role and responsibilities",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive positions are hidden from dropdowns",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "Job Position"
        verbose_name_plural = "Job Positions"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate code from title if not provided
        if not self.code:
            self.code = slugify(self.title).replace("-", "_").upper()[:50]
        super().save(*args, **kwargs)