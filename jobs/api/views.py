from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

# Django
from django.shortcuts import render, get_object_or_404

# Use absolute import for models to avoid relative-import confusion
from jobs.models import Job, JobRecord, JobAttachment

# Serializers (same package)
from .serializers import JobSerializer, JobRecordSerializer, JobAttachmentSerializer

from rest_framework.permissions import IsAuthenticatedOrReadOnly


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.select_related("branch", "service", "created_by").all()
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        job = self.get_object()
        job.status = "in_progress"
        job.save(update_fields=["status"])
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        job = self.get_object()
        job.status = "completed"
        job.save(update_fields=["status"])
        return Response(self.get_serializer(job).data)


class JobRecordViewSet(viewsets.ModelViewSet):
    queryset = JobRecord.objects.select_related("job", "performed_by").all()
    serializer_class = JobRecordSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        request = self.request
        if request.user and request.user.is_authenticated:
            if not serializer.validated_data.get("performed_by"):
                serializer.save(performed_by=request.user)
                return
        serializer.save()

    @action(detail=True, methods=["post"], parser_classes=(MultiPartParser, FormParser))
    def upload_attachment(self, request, pk=None):
        record = self.get_object()
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        att = JobAttachment.objects.create(
            record=record,
            file=file_obj,
            uploaded_by=request.user if request.user.is_authenticated else None,
            note=request.data.get("note", "")
        )
        return Response(JobAttachmentSerializer(att, context={"request": request}).data, status=status.HTTP_201_CREATED)


class JobAttachmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JobAttachment.objects.select_related("record__job").all()
    serializer_class = JobAttachmentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# --- server-rendered receipt view ---
def job_receipt(request, job_id):
    """
    Renders jobs/receipt.html with the Job instance.
    URL: e.g. /api/jobs/receipt/<job_id>/
    """
    job = get_object_or_404(Job, pk=job_id)
    return render(request, "jobs/receipt.html", {"job": job})
