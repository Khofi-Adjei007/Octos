from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .api.views import JobViewSet, JobRecordViewSet, JobAttachmentViewSet, job_receipt
from .views import attendant_dashboard

router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")
router.register(r"job-records", JobRecordViewSet, basename="job-record")
router.register(r"job-attachments", JobAttachmentViewSet, basename="job-attachment")

urlpatterns = [
    path("", include(router.urls)),
    path("receipt/<int:job_id>/", job_receipt, name="job_receipt"),
    path("ui/attendant/", attendant_dashboard, name="attendant_dashboard"),
]
