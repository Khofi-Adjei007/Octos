# public/api/views.py
from rest_framework import generics, permissions
from Human_Resources.models import PublicApplication
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
