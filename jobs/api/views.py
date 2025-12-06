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

logger = logging.getLogger(__name__)

# Models
Job = apps.get_model("jobs", "Job")
JobRecord = apps.get_model("jobs", "JobRecord")
JobAttachment = apps.get_model("jobs", "JobAttachment")

# Serializers
from .serializers import JobSerializer, JobRecordSerializer, JobAttachmentSerializer

# Services (class-based)
from jobs.services import job_service, shift_service, daysheet_service, anomaly_service

# Permission helper: use IsAuthenticated for unsafe methods
class ReadWritePermissionMixin:
    def get_permissions(self):
        # read-only is open, writes require authentication
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated()]


class JobViewSet(ReadWritePermissionMixin, viewsets.ModelViewSet):
    """
    Job endpoint. Creation of instant jobs is delegated to job_service.create_instant_job.
    Non-instant jobs have their unit_price snapshot preserved and are attached to the day's DaySheet.
    """
    queryset = Job.objects.select_related("branch", "service", "created_by").all()
    serializer_class = JobSerializer

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def start(self, request, pk=None):
        job = self.get_object()
        if job.status == "in_progress":
            return Response({"detail": "Job already in progress"}, status=status.HTTP_400_BAD_REQUEST)
        job.status = "in_progress"
        job.save(update_fields=["status"])
        # status log and shadow event created inside services where needed; minimal here
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        """
        Mark job completed and create a JobRecord summarizing completion.
        Wrap in a transaction to keep job status + record creation + daysheet attach atomic.
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

                # create a completion record (best-effort but inside txn)
                try:
                    JobRecord.objects.create(
                        job=job,
                        performed_by=request.user if request.user.is_authenticated else None,
                        time_start=now,
                        time_end=now,
                        quantity_produced=getattr(job, "quantity", 1) or 1,
                        notes="Marked completed via API",
                    )
                except Exception as exc:
                    # log but allow transaction to continue — we don't want a missing attachment to block completion
                    logger.exception("Failed to create completion JobRecord for job %s: %s", getattr(job, "pk", None), exc)

                # Ensure job is attached to daysheet (idempotent)
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
        Ensure performed_by is set, attach job to daysheet, run lightweight anomaly detection.
        Save once with performed_by when needed.
        """
        request = self.request
        user = request.user if request.user.is_authenticated else None

        save_kwargs = {}
        if not serializer.validated_data.get("performed_by") and user:
            save_kwargs["performed_by"] = user

        try:
            # save the record (single save)
            instance = serializer.save(**save_kwargs)
        except Exception as exc:
            logger.exception("Failed to save JobRecord via API: %s", exc)
            raise

        # after save we can attach to daysheet and run detectors
        try:
            job = getattr(instance, "job", None)
            if job:
                # Attach job to daysheet idempotently (updates totals)
                try:
                    job_service.attach_job_to_daysheet_idempotent(job, user=user, now=timezone.now())
                except Exception as exc:
                    logger.exception("attach_job_to_daysheet_idempotent failed for job %s: %s", getattr(job, "pk", None), exc)

                # Basic duplicate detection (best-effort)
                try:
                    anomaly_service.detect_duplicate_job(job)
                except Exception as exc:
                    logger.debug("anomaly_service.detect_duplicate_job raised: %s", exc)
        except Exception as exc:
            logger.exception("Post-save hooks for JobRecord failed: %s", exc)
            # do not re-raise; we don't want post-save hooks to crash the API response

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


# --- server-rendered receipt view kept for backward compatibility ---
def job_receipt(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    return render(request, "jobs/receipt.html", {"job": job})
