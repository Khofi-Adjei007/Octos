# jobs/models.py
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

User = settings.AUTH_USER_MODEL

# -----------------------
# Status / priority (existing)
# -----------------------
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
    job_id = getattr(getattr(instance, "record", None), "job_id", "unknown")
    ts = timezone.now().strftime("%Y%m%d_%H%M%S")
    return f"jobs/{job_id}/attachments/{ts}_{filename}"


# -----------------------
# Daily operational sheet for a branch (upgraded version)
# -----------------------
class DaySheet(models.Model):
    STATUS_OPEN = "open"
    STATUS_PARTIALLY_CLOSED = "partially_closed"
    STATUS_BRANCH_CLOSED = "branch_closed"
    STATUS_HQ_CLOSED = "hq_closed"
    STATUS_AUTO_CLOSED = "auto_closed"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_PARTIALLY_CLOSED, "Partially Closed"),
        (STATUS_BRANCH_CLOSED, "Branch Closed"),
        (STATUS_HQ_CLOSED, "HQ Closed"),
        (STATUS_AUTO_CLOSED, "Auto Closed"),
    ]

    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="daysheets")
    date = models.DateField(help_text="Local date for the sheet (branch timezone)")
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    opened_at = models.DateTimeField(auto_now_add=True)

    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="+", on_delete=models.SET_NULL)
    closed_at = models.DateTimeField(null=True, blank=True)

    hq_closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="hq_closed_sheets", on_delete=models.SET_NULL)
    hq_closed_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_OPEN)
    meta = models.JSONField(default=dict, blank=True)

    total_jobs = models.PositiveIntegerField(default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    weekday = models.CharField(max_length=12, blank=True)
    branch_name = models.CharField(max_length=200, blank=True)
    branch_city = models.CharField(max_length=120, blank=True)
    branch_manager_name = models.CharField(max_length=150, blank=True)
    branch_manager_email = models.EmailField(blank=True)

    opening_cash = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    closing_cash = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    cash_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    momo_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    card_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    deposits_total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    report_url = models.CharField(max_length=1024, blank=True, default="")

    shift_name = models.CharField(max_length=64, blank=True, null=True)
    locked = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("branch", "date"),)
        ordering = ("-date",)

    def __str__(self):
        return f"DaySheet {self.branch} - {self.date} ({self.status})"


# -----------------------
# DaySheetShift (upgraded)
# -----------------------
class DaySheetShift(models.Model):
    SHIFT_OPEN = "shift_open"
    SHIFT_CLOSED = "shift_closed"
    SHIFT_AUTO_CLOSED = "shift_auto_closed"
    SHIFT_LOCKED = "locked"

    SHIFT_STATUS_CHOICES = [
        (SHIFT_OPEN, "Open"),
        (SHIFT_CLOSED, "Closed"),
        (SHIFT_AUTO_CLOSED, "Auto Closed"),
        (SHIFT_LOCKED, "Locked"),
    ]

    daysheet = models.ForeignKey(DaySheet, on_delete=models.CASCADE, related_name="shifts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    role = models.CharField(max_length=64, blank=True)
    shift_start = models.DateTimeField(null=True, blank=True)
    shift_end = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=24, choices=SHIFT_STATUS_CHOICES, default=SHIFT_OPEN)
    submitted = models.BooleanField(default=False)
    opening_cash = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    closing_cash = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    pin_verified_at = models.DateTimeField(null=True, blank=True)
    pin_verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="pin_verified_shifts", on_delete=models.SET_NULL)
    pin_failed_attempts = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["daysheet", "user"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Shift {self.user} on {self.daysheet.date} ({self.status})"


# -----------------------
# Job model (existing)
# -----------------------
class Job(models.Model):
    """
    Walk-in job / work order scheduled at a branch.

    - `type` distinguishes INSTANT (completed immediately by attendant) vs QUEUED (processed later).
    - `unit_price` is a snapshot of the service price at creation time.
    - `total_amount` = unit_price * quantity - deposit_amount (stored for receipts / daily sales).
    """
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="jobs")
    service = models.ForeignKey("branches.ServiceType", on_delete=models.PROTECT, related_name="jobs")
    daysheet = models.ForeignKey(DaySheet, null=True, blank=True, on_delete=models.SET_NULL, related_name="jobs")
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

    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    expected_minutes_per_unit = models.PositiveIntegerField(null=True, blank=True,
                                                          help_text="Minutes to complete one unit (overrides service.meta)")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)

    type = models.CharField(max_length=16, choices=JOB_TYPE_CHOICES, default=JOB_TYPE_QUEUED)

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    queue_position = models.PositiveIntegerField(null=True, blank=True)
    expected_ready_at = models.DateTimeField(null=True, blank=True)

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
        if self.expected_minutes_per_unit:
            return int(self.expected_minutes_per_unit)
        meta = getattr(self.service, "meta", {}) or {}
        return int(meta.get("avg_minutes_per_unit", 30))

    def estimated_total_minutes(self):
        return self.compute_expected_minutes() * max(1, self.quantity)

    def snapshot_price_and_total(self):
        if self.unit_price is None:
            svc_price = getattr(self.service, "price", None)
            if svc_price is None:
                svc_price = self.price or Decimal("0.00")
            self.unit_price = Decimal(svc_price or 0)

        if self.total_amount is None:
            total = (Decimal(self.unit_price or 0) * Decimal(max(1, self.quantity))) - Decimal(self.deposit_amount or 0)
            if total < 0:
                total = Decimal("0.00")
            self.total_amount = total.quantize(Decimal("0.01"))


# -----------------------
# JobRecord model (existing)
# -----------------------
class JobRecord(models.Model):
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


# -----------------------
# JobAttachment model (existing)
# -----------------------
class JobAttachment(models.Model):
    record = models.ForeignKey(JobRecord, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=job_attachment_upload_path)
    uploaded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


# -----------------------
# DailySale (existing)
# -----------------------
class DailySale(models.Model):
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="daily_sales")
    date = models.DateField(db_index=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total_count = models.PositiveIntegerField(default=0)
    meta = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("branch", "date"),)
        ordering = ("-date",)


# -----------------------
# NEW: CorrectionEntry
# -----------------------
class CorrectionEntry(models.Model):
    TYPE_AMOUNT_CORRECTION = "amount_correction"
    TYPE_NOTE = "note"
    TYPE_DISPUTE = "dispute"
    TYPE_RECONCILIATION = "reconciliation_adjustment"

    TYPE_CHOICES = [
        (TYPE_AMOUNT_CORRECTION, "Amount Correction"),
        (TYPE_NOTE, "Note"),
        (TYPE_DISPUTE, "Dispute"),
        (TYPE_RECONCILIATION, "Reconciliation Adjustment"),
    ]

    STATUS_OPEN = "open"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_ESCALATED = "escalated"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_ESCALATED, "Escalated"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    daily_sheet = models.ForeignKey(DaySheet, on_delete=models.CASCADE, related_name="corrections")
    shift = models.ForeignKey(DaySheetShift, null=True, blank=True, on_delete=models.SET_NULL, related_name="corrections")
    job = models.ForeignKey(Job, null=True, blank=True, on_delete=models.SET_NULL, related_name="corrections")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="corrections_created")
    created_for_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="corrections_for")
    type = models.CharField(max_length=48, choices=TYPE_CHOICES, default=TYPE_NOTE)
    payload = models.JSONField(default=dict, blank=True, help_text="Structured correction details (immutable)")
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_OPEN)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="corrections_approved", on_delete=models.SET_NULL)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Correction {self.type} ({self.status}) for sheet {self.daily_sheet_id}"


# -----------------------
# NEW: StatusLog (local audit trail)
# -----------------------
class StatusLog(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    entity_type = models.CharField(max_length=64)
    entity_id = models.CharField(max_length=128)
    event = models.CharField(max_length=128)
    actor_id = models.CharField(max_length=128, blank=True, null=True)
    actor_role = models.CharField(max_length=64, blank=True, null=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["event"]),
        ]

    def __str__(self):
        return f"StatusLog {self.event} @ {self.entity_type}:{self.entity_id}"


# -----------------------
# NEW: ShadowLogEvent (immutable, sent to HQ)
# -----------------------
class ShadowLogEvent(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    event_type = models.CharField(max_length=128)
    branch_id = models.CharField(max_length=128, blank=True, null=True)
    source = models.JSONField(default=dict, blank=True)
    actor = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    payload = models.JSONField(default=dict, blank=True)
    signature = models.CharField(max_length=512, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-timestamp",)
        indexes = [
            models.Index(fields=["event_type"]),
            models.Index(fields=["branch_id"]),
        ]

    def __str__(self):
        return f"ShadowEvent {self.event_type} @ {self.timestamp.isoformat()}"


# -----------------------
# NEW: AnomalyFlag (fixed)
# -----------------------
class AnomalyFlag(models.Model):
    SEV_INFO = "info"
    SEV_MEDIUM = "medium"
    SEV_HIGH = "high"
    SEV_CRITICAL = "critical"

    SEVERITY_CHOICES = [
        (SEV_INFO, "Info"),
        (SEV_MEDIUM, "Medium"),
        (SEV_HIGH, "High"),
        (SEV_CRITICAL, "Critical"),
    ]

    TYPE_AUTO_CLOSE = "auto_close"
    TYPE_MISMATCH_CASH = "mismatch_cash"
    TYPE_HIGH_FREE_JOBS = "high_free_jobs"
    TYPE_DUPLICATE_JOBS = "duplicate_jobs"
    TYPE_REPEATED_CORRECTIONS = "repeated_corrections"
    TYPE_CUSTOM = "custom"

    FLAG_TYPE_CHOICES = [
        (TYPE_AUTO_CLOSE, "Auto Close"),
        (TYPE_MISMATCH_CASH, "Mismatch Cash"),
        (TYPE_HIGH_FREE_JOBS, "High Free Jobs"),
        (TYPE_DUPLICATE_JOBS, "Duplicate Jobs"),
        (TYPE_REPEATED_CORRECTIONS, "Repeated Corrections"),
        (TYPE_CUSTOM, "Custom"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    daily_sheet = models.ForeignKey(DaySheet, null=True, blank=True, on_delete=models.CASCADE, related_name="anomalies")
    shift = models.ForeignKey(DaySheetShift, null=True, blank=True, on_delete=models.SET_NULL, related_name="anomalies")
    flag_type = models.CharField(max_length=64, choices=FLAG_TYPE_CHOICES, default=TYPE_CUSTOM)
    severity = models.CharField(max_length=32, choices=SEVERITY_CHOICES, default=SEV_MEDIUM)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notified_to = models.JSONField(default=list, blank=True, help_text="List of roles/users notified")

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Anomaly {self.flag_type} ({self.severity}) on sheet {getattr(self.daily_sheet, 'id', None)}"
