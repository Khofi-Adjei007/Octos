# jobs/api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.shortcuts import render, get_object_or_404
from django.apps import apps
from django.utils import timezone
from django.db import transaction
import logging

from .serializers import JobSerializer, JobRecordSerializer, JobAttachmentSerializer
from jobs.services import job_service, shift_service, daysheet_service, anomaly_service

logger = logging.getLogger(__name__)

# Models
Job = apps.get_model("jobs", "Job")
JobRecord = apps.get_model("jobs", "JobRecord")
JobAttachment = apps.get_model("jobs", "JobAttachment")


class ReadWritePermissionMixin:
    """
    Returns readable permissions for safe methods and stricter permissions for unsafe ones.
    Instances (not classes) are returned as DRF expects permission instances.
    """
    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated()]


class JobViewSet(ReadWritePermissionMixin, viewsets.ModelViewSet):
    """
    Job endpoint. Creation of instant jobs is delegated to job_service.create_instant_job via serializer.
    Non-instant jobs snapshot unit_price/total and are attached to the day's DaySheet.
    """
    queryset = Job.objects.select_related("branch", "service", "created_by").all()
    serializer_class = JobSerializer

    def get_queryset(self):
        """
        Allow optional filtering by branch via ?branch=<id> to make dashboard wiring easy.
        """
        qs = super().get_queryset()
        branch = self.request.query_params.get("branch")
        if branch:
            try:
                branch_id = int(branch)
                qs = qs.filter(branch_id=branch_id)
            except Exception:
                pass
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        # ensure request is present in serializer context for job_service delegation
        ctx["request"] = self.request
        return ctx

    def perform_create(self, serializer):
        """
        Ensure created_by set when available. The serializer's create() will delegate instant-job
        creation to job_service, but for queued jobs we still pass created_by as a kwarg so the
        serializer/create has consistent info.
        """
        user = self.request.user if self.request and getattr(self.request, "user", None) and self.request.user.is_authenticated else None
        try:
            serializer.save(created_by=user)
        except Exception as exc:
            logger.exception("Job create failed: %s", exc)
            raise

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def start(self, request, pk=None):
        job = self.get_object()
        if job.status == "in_progress":
            return Response({"detail": "Job already in progress"}, status=status.HTTP_400_BAD_REQUEST)
        job.status = "in_progress"
        job.save(update_fields=["status"])
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        """
        Mark job completed, create a JobRecord, and attach job to daysheet in a transaction.
        """
        job = self.get_object()
        if job.status == "completed":
            return Response({"detail": "Job already completed"}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        try:
            with transaction.atomic():
                job.status = "completed"
                job.completed_at = now
                job.save(update_fields=["status", "completed_at"])

                # Best-effort record creation (kept inside txn but guarded)
                try:
                    JobRecord.objects.create(
                        job=job,
                        performed_by=request.user if request.user and request.user.is_authenticated else None,
                        time_start=now,
                        time_end=now,
                        quantity_produced=getattr(job, "quantity", 1) or 1,
                        notes="Marked completed via API",
                    )
                except Exception as exc:
                    logger.exception("Failed to create completion JobRecord for job %s: %s", getattr(job, "pk", None), exc)

                # Idempotent attach to daysheet
                try:
                    job_service.attach_job_to_daysheet_idempotent(job, user=request.user, now=now)
                except Exception as exc:
                    logger.exception("Failed to attach job %s to daysheet during complete action: %s", getattr(job, "pk", None), exc)
        except Exception as exc:
            logger.exception("Failed to complete job %s: %s", getattr(job, "pk", None), exc)
            return Response({"detail": "Failed to complete job", "error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(self.get_serializer(job).data)


class JobRecordViewSet(ReadWritePermissionMixin, viewsets.ModelViewSet):
    queryset = JobRecord.objects.select_related("job", "performed_by").all()
    serializer_class = JobRecordSerializer
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        """
        Save record, attach job to daysheet idempotently, then run anomaly detectors.
        """
        request = self.request
        user = request.user if request.user and request.user.is_authenticated else None

        save_kwargs = {}
        if not serializer.validated_data.get("performed_by") and user:
            save_kwargs["performed_by"] = user

        try:
            instance = serializer.save(**save_kwargs)
        except Exception as exc:
            logger.exception("Failed to save JobRecord via API: %s", exc)
            raise

        # post-save hooks (best-effort)
        try:
            job = getattr(instance, "job", None)
            if job:
                try:
                    job_service.attach_job_to_daysheet_idempotent(job, user=user, now=timezone.now())
                except Exception as exc:
                    logger.exception("attach_job_to_daysheet_idempotent failed for job %s: %s", getattr(job, "pk", None), exc)
                try:
                    anomaly_service.detect_duplicate_job(job)
                except Exception as exc:
                    logger.debug("anomaly_service.detect_duplicate_job raised: %s", exc)
        except Exception as exc:
            logger.exception("Post-save hooks for JobRecord failed: %s", exc)

    @action(detail=True, methods=["post"], parser_classes=(MultiPartParser, FormParser), permission_classes=[IsAuthenticated])
    def upload_attachment(self, request, pk=None):
        record = self.get_object()
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            att = JobAttachment.objects.create(
                record=record,
                file=file_obj,
                uploaded_by=request.user if request.user.is_authenticated else None,
                note=request.data.get("note", "")
            )
            serializer = JobAttachmentSerializer(att, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            logger.exception("Failed to save attachment for JobRecord %s: %s", getattr(record, "pk", None), exc)
            return Response({"detail": "Attachment save failed", "error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class JobAttachmentViewSet(ReadWritePermissionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = JobAttachment.objects.select_related("record__job").all()
    serializer_class = JobAttachmentSerializer


def job_receipt(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    return render(request, "jobs/receipt.html", {"job": job})
