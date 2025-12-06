# jobs/admin.py
from django.contrib import admin
from django.utils import timezone
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

def get_model_safe(app_label: str, model_name: str):
    """Return model class or None if not available (avoids LookupError during startup)."""
    try:
        return apps.get_model(app_label, model_name)
    except (LookupError, ImproperlyConfigured):
        return None

# lazy model resolution
Job = get_model_safe("jobs", "Job")
JobRecord = get_model_safe("jobs", "JobRecord")
JobAttachment = get_model_safe("jobs", "JobAttachment")
DailySale = get_model_safe("jobs", "DailySale")

DaySheet = get_model_safe("jobs", "DaySheet")
DaySheetShift = get_model_safe("jobs", "DaySheetShift")
CorrectionEntry = get_model_safe("jobs", "CorrectionEntry")
StatusLog = get_model_safe("jobs", "StatusLog")
ShadowLogEvent = get_model_safe("jobs", "ShadowLogEvent")
AnomalyFlag = get_model_safe("jobs", "AnomalyFlag")


# ---------- existing models (preserved) ----------
if Job is not None:
    @admin.register(Job)
    class JobAdmin(admin.ModelAdmin):
        list_display = ("id", "service", "branch", "customer_name", "status", "queue_position", "expected_ready_at")
        list_filter = ("status", "branch", "service", "priority", "type")
        search_fields = ("customer_name", "customer_phone", "description", "id")
        readonly_fields = ("created_at", "updated_at")


if JobRecord is not None:
    @admin.register(JobRecord)
    class JobRecordAdmin(admin.ModelAdmin):
        list_display = ("id", "job", "performed_by", "time_start", "time_end", "quantity_produced")
        search_fields = ("job__id", "performed_by__username")
        readonly_fields = ("created_at",)


if JobAttachment is not None:
    @admin.register(JobAttachment)
    class JobAttachmentAdmin(admin.ModelAdmin):
        list_display = ("id", "record", "uploaded_by", "file", "created_at")
        readonly_fields = ("created_at",)


if DailySale is not None:
    @admin.register(DailySale)
    class DailySaleAdmin(admin.ModelAdmin):
        list_display = ("branch", "date", "total_amount", "total_count")
        list_filter = ("branch", "date")
        readonly_fields = ("updated_at",)


# ---------- new models (conditionally registered) ----------
if DaySheet is not None:
    @admin.register(DaySheet)
    class DaySheetAdmin(admin.ModelAdmin):
        list_display = ("id", "branch", "date", "status", "total_jobs", "total_amount", "created_at", "closed_at")
        list_filter = ("status", "branch", "date")
        search_fields = ("branch_name", "branch_city", "branch_manager_name", "date")
        readonly_fields = (
            "created_at",
            "updated_at",
            "opened_by",
            "opened_at",
            "hq_closed_by",
            "hq_closed_at",
            "report_url",
        )

        fieldsets = (
            (None, {
                "fields": ("branch", "date", "status", "notes", "meta", "report_url")
            }),
            ("Totals", {
                "fields": ("total_jobs", "total_amount", "opening_cash", "closing_cash",
                           "cash_total", "momo_total", "card_total", "deposits_total")
            }),
            ("Audit", {
                "fields": ("opened_by", "opened_at", "closed_by", "closed_at", "hq_closed_by", "hq_closed_at", "created_at", "updated_at")
            }),
        )

        def has_delete_permission(self, request, obj=None):
            # preserve data integrity via admin — disallow deletes here by default
            return False


if DaySheetShift is not None:
    @admin.register(DaySheetShift)
    class DaySheetShiftAdmin(admin.ModelAdmin):
        list_display = ("id", "daysheet", "user", "role", "status", "shift_start", "shift_end", "closing_cash", "pin_verified_at")
        list_filter = ("status", "role")
        search_fields = ("user__username", "user__first_name", "user__last_name")
        readonly_fields = ("created_at", "updated_at", "pin_verified_at", "pin_verified_by", "pin_failed_attempts")

        def has_delete_permission(self, request, obj=None):
            return False


if CorrectionEntry is not None:
    @admin.register(CorrectionEntry)
    class CorrectionEntryAdmin(admin.ModelAdmin):
        list_display = ("id", "type", "status", "daily_sheet", "shift", "job", "created_by", "created_at", "approved_by", "approved_at")
        list_filter = ("type", "status", "created_at")
        search_fields = ("payload", "created_by__username", "created_for_user__username")
        readonly_fields = ("created_at", "approved_at", "created_by")

        actions = ["mark_approved", "mark_rejected"]

        def mark_approved(self, request, queryset):
            updated = queryset.filter(status=CorrectionEntry.STATUS_OPEN).update(
                status=CorrectionEntry.STATUS_APPROVED,
                approved_by=request.user,
                approved_at=timezone.now(),
            )
            self.message_user(request, f"{updated} correction(s) marked as approved.")
        mark_approved.short_description = "Mark selected corrections as APPROVED"

        def mark_rejected(self, request, queryset):
            updated = queryset.filter(status=CorrectionEntry.STATUS_OPEN).update(status=CorrectionEntry.STATUS_REJECTED)
            self.message_user(request, f"{updated} correction(s) marked as rejected.")
        mark_rejected.short_description = "Mark selected corrections as REJECTED"

        def has_delete_permission(self, request, obj=None):
            return False


if StatusLog is not None:
    @admin.register(StatusLog)
    class StatusLogAdmin(admin.ModelAdmin):
        list_display = ("id", "event", "entity_type", "entity_id", "actor_id", "created_at")
        list_filter = ("event", "entity_type")
        search_fields = ("payload", "actor_id", "entity_id")
        readonly_fields = ("created_at", "payload")

        def has_add_permission(self, request):
            # programmatically created only
            return False

        def has_delete_permission(self, request, obj=None):
            return False


if ShadowLogEvent is not None:
    @admin.register(ShadowLogEvent)
    class ShadowLogEventAdmin(admin.ModelAdmin):
        list_display = ("id", "event_type", "branch_id", "timestamp", "sent_at", "received_at", "processed_at")
        list_filter = ("event_type", "branch_id")
        search_fields = ("payload", "branch_id", "event_type")
        readonly_fields = ("payload", "signature", "timestamp", "sent_at", "received_at", "processed_at")

        def has_add_permission(self, request):
            return False

        def has_delete_permission(self, request, obj=None):
            return False


if AnomalyFlag is not None:
    @admin.register(AnomalyFlag)
    class AnomalyFlagAdmin(admin.ModelAdmin):
        list_display = ("id", "flag_type", "severity", "daily_sheet", "shift", "description", "created_at")
        list_filter = ("flag_type", "severity")
        search_fields = ("description",)
        readonly_fields = ("created_at", "notified_to")

        def has_delete_permission(self, request, obj=None):
            return False
