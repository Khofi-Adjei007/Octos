# public/api/urls.py
from django.urls import path
from .views import PublicApplicationCreateView

urlpatterns = [
    path("applications/", PublicApplicationCreateView.as_view(), name="api-public-apply"),
]
