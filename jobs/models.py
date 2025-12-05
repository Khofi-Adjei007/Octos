# jobs/models.py  -- append or merge with your existing file
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

User = settings.AUTH_USER_MODEL

# ---------- extended DaySheet state (backwards-compatible) ----------
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

    # existing fields kept
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="daysheets")
    date = models.DateField(help_text="Local date for the sheet (branch timezone)")
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    opened_at = models.DateTimeField(auto_now_add=True)

    # keep existing closed_by/closed_at for manager close
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="+", on_delete=models.SET_NULL)
    closed_at = models.DateTimeField(null=True, blank=True)

    # new: hq close fields
    hq_closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="hq_closed_sheets", on_delete=models.SET_NULL)
    hq_closed_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_OPEN)
    meta = models.JSONField(default=dict, blank=True)

    # existing totals
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

    # optional: summary/report url or file ref
    report_url = models.CharField(max_length=1024, blank=True, default="")

    shift_name = models.CharField(max_length=64, blank=True, null=True)
    locked = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # helpful for auditing

    class Meta:
        unique_together = (("branch", "date"),)
        ordering = ("-date",)

    def __str__(self):
        return f"DaySheet {self.branch} - {self.date} ({self.status})"


# ---------- DaySheetShift (upgraded) ----------
class DaySheetShift(models.Model):
    # shift states
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
    role = models.CharField(max_length=64, blank=True)   # e.g., ATTENDANT, CASHIER
    shift_start = models.DateTimeField(null=True, blank=True)
    shift_end = models.DateTimeField(null=True, blank=True)

    # new: explicit status and pin audit
    status = models.CharField(max_length=24, choices=SHIFT_STATUS_CHOICES, default=SHIFT_OPEN)
    submitted = models.BooleanField(default=False)      # attendant submitted their shift (legacy field)
    opening_cash = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    closing_cash = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    # PIN verification: store metadata only (do NOT store raw PIN)
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


# ---------- CorrectionEntry (append-only corrections / claims) ----------
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

    id = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    daily_sheet = models.ForeignKey(DaySheet, on_delete=models.CASCADE, related_name="corrections")
    shift = models.ForeignKey(DaySheetShift, null=True, blank=True, on_delete=models.SET_NULL, related_name="corrections")
    job = models.ForeignKey("Job", null=True, blank=True, on_delete=models.SET_NULL, related_name="corrections")
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
        return f"Correction {self.type} for sheet {self.daily_sheet_id} ({self.status})"


# ---------- StatusLog (local audit trail) ----------
class StatusLog(models.Model):
    id = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    entity_type = models.CharField(max_length=64)  # e.g., DaySheet, DaySheetShift, Job, CorrectionEntry
    entity_id = models.CharField(max_length=128)   # store PK as string for cross-model reference
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


# ---------- ShadowLogEvent (immutable, sent to HQ) ----------
class ShadowLogEvent(models.Model):
    id = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=128)
    branch_id = models.CharField(max_length=128, blank=True, null=True)
    source = models.JSONField(default=dict, blank=True)   # device_id, server_instance, ip, etc.
    actor = models.JSONField(default=dict, blank=True)    # user_id, role, pin_used?
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


# ---------- AnomalyFlag ----------
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

    id = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
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
# ---------- end of jobs/models.py ----------