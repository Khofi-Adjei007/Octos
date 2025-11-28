from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

User = settings.AUTH_USER_MODEL

STATUS_QUEUED = "queued"
STATUS_IN_PROGRESS = "in_progress"
STATUS_READY = "ready"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"
STATUS_CHOICES = [
    (STATUS_QUEUED, "Queued"),
    (STATUS_IN_PROGRESS, "In Progress"),
    (STATUS_READY, "Ready"),
    (STATUS_COMPLETED, "Completed"),
    (STATUS_CANCELLED, "Cancelled"),
]

PRIORITY_NORMAL = "normal"
PRIORITY_EXPRESS = "express"
PRIORITY_CHOICES = [(PRIORITY_NORMAL, "Normal"), (PRIORITY_EXPRESS, "Express")]


def job_attachment_upload_path(instance, filename):
    return f"jobs/{instance.record.job.id}/attachments/{timezone.now().strftime('%Y%m%d_%H%M%S')}_{filename}"


class Job(models.Model):
    """
    Walk-in job / work order scheduled at a branch.
    """
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="jobs")
    service = models.ForeignKey("branches.ServiceType", on_delete=models.PROTECT, related_name="jobs")
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=32, blank=True, null=True)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expected_minutes_per_unit = models.PositiveIntegerField(null=True, blank=True,
                                                          help_text="Minutes to complete one unit (overrides service.meta)")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    queue_position = models.PositiveIntegerField(null=True, blank=True)
    expected_ready_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="jobs_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["branch", "status", "expected_ready_at"])]

    def __str__(self):
        return f"Job#{self.pk or '?'} {self.service} @ {self.branch} for {self.customer_name}"

    def compute_expected_minutes(self):
        # priority: explicit field -> service.meta.avg_minutes_per_unit -> default 30
        if self.expected_minutes_per_unit:
            return int(self.expected_minutes_per_unit)
        meta = getattr(self.service, "meta", {}) or {}
        return int(meta.get("avg_minutes_per_unit", 30))

    def estimated_total_minutes(self):
        return self.compute_expected_minutes() * max(1, self.quantity)


class JobRecord(models.Model):
    """
    Log of actual work done for a Job (one or more records per Job allowed).
    """
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="records")
    performed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="job_records")
    time_start = models.DateTimeField()
    time_end = models.DateTimeField(null=True, blank=True)
    quantity_produced = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    issues = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def duration_seconds(self):
        if self.time_end and self.time_start:
            return (self.time_end - self.time_start).total_seconds()
        return None


class JobAttachment(models.Model):
    record = models.ForeignKey(JobRecord, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=job_attachment_upload_path)
    uploaded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
