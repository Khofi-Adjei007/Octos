from django.contrib import admin
from .models import Job, JobRecord, JobAttachment

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "service", "branch", "customer_name", "status", "queue_position", "expected_ready_at")
    list_filter = ("status", "branch", "service", "priority")
    search_fields = ("customer_name", "customer_phone", "description", "id")

@admin.register(JobRecord)
class JobRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "performed_by", "time_start", "time_end", "quantity_produced")
    search_fields = ("job__id", "performed_by__username")

@admin.register(JobAttachment)
class JobAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "record", "uploaded_by", "file", "created_at")
