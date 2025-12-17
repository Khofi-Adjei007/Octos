# jobs/api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.views import APIView

from django.shortcuts import render, get_object_or_404
from django.apps import apps
from django.utils import timezone
from django.db import transaction
import logging

from .serializers import (
    JobSerializer,
    JobRecordSerializer,
    JobAttachmentSerializer,
    ServiceTypeSerializer,
    ServicePricingRuleSerializer,
)

from jobs.services import job_service, shift_service, daysheet_service, anomaly_service

logger = logging.getLogger(__name__)

# =========================
# Models
# =========================
Job = apps.get_model("jobs", "Job")
JobRecord = apps.get_model("jobs", "JobRecord")
JobAttachment = apps.get_model("jobs", "JobAttachment")
ServiceType = apps.get_model("jobs", "ServiceType")
ServicePricingRule = apps.get_model("jobs", "ServicePricingRule")


# =========================
# Permission mixin
# =========================
class ReadWritePermissionMixin:
    """
    Safe methods are readable, unsafe methods require authentication.
    """
    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated()]


# =========================
# Job APIs
# =========================
class JobViewSet(ReadWritePermissionMixin, viewsets.ModelViewSet):
    queryset = Job.objects.select_related("branch", "service", "created_by").all()
    serializer_class = JobSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        branch = self.request.query_params.get("branch")
        if branch:
            try:
                qs = qs.filter(branch_id=int(branch))
            except Exception:
                pass
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def start(self, request, pk=None):
        job = self.get_object()
        if job.status == "in_progress":
            return Response(
                {"detail": "Job already in progress"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        job.status = "in_progress"
        job.save(update_fields=["status"])
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        job = self.get_object()
        if job.status == "completed":
            return Response(
                {"detail": "Job already completed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        with transaction.atomic():
            job.status = "completed"
            job.completed_at = now
            job.save(update_fields=["status", "completed_at"])

            try:
                JobRecord.objects.create(
                    job=job,
                    performed_by=request.user,
                    time_start=now,
                    time_end=now,
                    quantity_produced=job.quantity or 1,
                    notes="Marked completed via API",
                )
            except Exception:
                logger.exception("JobRecord creation failed during complete")

            try:
                job_service.attach_job_to_daysheet_idempotent(
                    job, user=request.user, now=now
                )
            except Exception:
                logger.exception("attach_job_to_daysheet_idempotent failed during complete")

        return Response(self.get_serializer(job).data)


class JobRecordViewSet(ReadWritePermissionMixin, viewsets.ModelViewSet):
    queryset = JobRecord.objects.select_related("job", "performed_by").all()
    serializer_class = JobRecordSerializer
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        instance = serializer.save(performed_by=user)
        try:
            job_service.attach_job_to_daysheet_idempotent(
                instance.job, user=user, now=timezone.now()
            )
            anomaly_service.detect_duplicate_job(instance.job)
        except Exception:
            logger.debug("Post JobRecord hooks failed")

    @action(
        detail=True,
        methods=["post"],
        parser_classes=(MultiPartParser, FormParser),
        permission_classes=[IsAuthenticated],
    )
    def upload_attachment(self, request, pk=None):
        record = self.get_object()
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response(
                {"detail": "No file uploaded"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        att = JobAttachment.objects.create(
            record=record,
            file=file_obj,
            uploaded_by=request.user,
            note=request.data.get("note", ""),
        )
        return Response(
            JobAttachmentSerializer(att).data,
            status=status.HTTP_201_CREATED,
        )


class JobAttachmentViewSet(ReadWritePermissionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = JobAttachment.objects.select_related("record__job").all()
    serializer_class = JobAttachmentSerializer


def job_receipt(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    return render(request, "jobs/receipt.html", {"job": job})


# ==================================================
# READ-ONLY APIs (SERVICES + PRICING)
# ==================================================

class ServiceTypeListAPIView(APIView):
    """
    Expose available services to the UI.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        services = ServiceType.objects.all().order_by("name")
        serializer = ServiceTypeSerializer(services, many=True)
        return Response(serializer.data)


class ServicePricingRuleListAPIView(APIView):
    """
    Expose pricing rules for a specific service.
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, service_id):
        rules = ServicePricingRule.objects.filter(
            service_id=service_id,
            is_active=True,
        ).order_by(
            "paper_size",
            "print_mode",
            "color_mode",
            "side_mode",
        )
        serializer = ServicePricingRuleSerializer(rules, many=True)
        return Response(serializer.data)
