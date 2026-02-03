# public/api/views.py
from rest_framework import generics, permissions
from Human_Resources.models.common import validate_resume_file
from hr_workflows.models import recruitment_legacy as rec_legacy
from hr_workflows.models.recruitment_legacy import PublicApplication
from .serializers import PublicApplicationSerializer

class PublicApplicationCreateView(generics.CreateAPIView):
    """
    Public endpoint: accept application from website/mobile.
    No auth required.
    """
    queryset = PublicApplication.objects.all()
    serializer_class = PublicApplicationSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        # created_by left null for public submissions
        serializer.save(created_by=None, status="pending")
