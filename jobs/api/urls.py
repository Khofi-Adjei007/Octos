# jobs/api/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import (
    JobViewSet,
    JobRecordViewSet,
    JobAttachmentViewSet,
    job_receipt,
    ServiceTypeListAPIView,
    ServicePricingRuleListAPIView,
)

router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")
router.register(r"job-records", JobRecordViewSet, basename="job-record")
router.register(r"job-attachments", JobAttachmentViewSet, basename="job-attachment")

app_name = "jobs_api"

urlpatterns = [
    # ----------------------------
    # Existing router-based APIs
    # ----------------------------
    path("", include(router.urls)),

    # Server-rendered receipt (backward compatibility)
    path("receipt/<int:job_id>/", job_receipt, name="job-receipt"),

    # ----------------------------
    # Services & Pricing APIs
    # ----------------------------
    path("services/", ServiceTypeListAPIView.as_view(), name="service-list"),
    path(
        "services/<int:service_id>/pricing/",
        ServicePricingRuleListAPIView.as_view(),
        name="service-pricing",
    ),
]
