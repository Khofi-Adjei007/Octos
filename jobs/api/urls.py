# jobs/api/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import JobViewSet, JobRecordViewSet, JobAttachmentViewSet, job_receipt

router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")
router.register(r"job-records", JobRecordViewSet, basename="job-record")
router.register(r"job-attachments", JobAttachmentViewSet, basename="job-attachment")

app_name = "jobs_api"

urlpatterns = [
    path("", include(router.urls)),
    # server-rendered receipt (kept for backward compatibility)
    path("receipt/<int:job_id>/", job_receipt, name="job-receipt"),
]
