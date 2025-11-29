from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

User = settings.AUTH_USER_MODEL

# Status / priority (existing)
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


# New: Job type (instant vs queued)
JOB_TYPE_INSTANT = "instant"
JOB_TYPE_QUEUED = "queued"
JOB_TYPE_CHOICES = [(JOB_TYPE_INSTANT, "Instant"), (JOB_TYPE_QUEUED, "Queued")]


def job_attachment_upload_path(instance, filename):
    # keep existing behaviour (use job id if available; fallback to timestamp)
    job_id = getattr(instance.record.job, "id", "unknown")
    ts = timezone.now().strftime("%Y%m%d_%H%M%S")
    return f"jobs/{job_id}/attachments/{ts}_{filename}"


class Job(models.Model):
    """
    Walk-in job / work order scheduled at a branch.

    - `type` distinguishes INSTANT (completed immediately by attendant) vs QUEUED (processed later).
    - `unit_price` is a snapshot of the service price at creation time.
    - `total_amount` = unit_price * quantity - deposit_amount (stored for receipts / daily sales).
    """
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="jobs")
    service = models.ForeignKey("branches.ServiceType", on_delete=models.PROTECT, related_name="jobs")
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=32, blank=True, null=True)
    description = models.TextField(blank=True)

    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    # existing price (optional) — keep for compatibility
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # new snapshot unit price and computed total
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                     help_text="Snapshot of service price when job was created")
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                       help_text="Computed total: unit_price * quantity - deposit_amount")

    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    expected_minutes_per_unit = models.PositiveIntegerField(null=True, blank=True,
                                                          help_text="Minutes to complete one unit (overrides service.meta)")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)

    # NEW: type instant vs queued (default queued to preserve existing behaviour)
    type = models.CharField(max_length=16, choices=JOB_TYPE_CHOICES, default=JOB_TYPE_QUEUED)

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    queue_position = models.PositiveIntegerField(null=True, blank=True)
    expected_ready_at = models.DateTimeField(null=True, blank=True)

    # NEW: completed timestamp for instant jobs (or when job finished)
    completed_at = models.DateTimeField(null=True, blank=True)

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

    def snapshot_price_and_total(self):
        """
        Helper: set unit_price and total_amount if not set.
        Should be called at creation time for INSTANT jobs (and optionally queued).
        """
        # prefer explicit unit_price if provided; else try service.price or job.price
        if self.unit_price is None:
            svc_price = getattr(self.service, "price", None)
            if svc_price is None:
                # fallback to job.price field (legacy)
                svc_price = self.price or Decimal("0.00")
            self.unit_price = Decimal(svc_price or 0)

        if self.total_amount is None:
            total = (Decimal(self.unit_price or 0) * Decimal(max(1, self.quantity))) - Decimal(self.deposit_amount or 0)
            # ensure non-negative
            if total < 0:
                total = Decimal("0.00")
            self.total_amount = total.quantize(Decimal("0.01"))


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


# NEW: Simple daily sales register to be incremented when an INSTANT job is created
class DailySale(models.Model):
    """
    Aggregated daily sales totals per branch.
    Business logic (in jobs_services) will create or update this when instant jobs are recorded.
    """
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="daily_sales")
    date = models.DateField(db_index=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_count = models.PositiveIntegerField(default=0)
    meta = models.JSONField(default=dict, blank=True)  # optional breakdown per service or cashier
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("branch", "date"),)
        ordering = ("-date",)
