from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import BranchViewSet

router = DefaultRouter()
router.register(r"branches", BranchViewSet, basename="branch")

urlpatterns = [
    path("", include(router.urls)),
]
