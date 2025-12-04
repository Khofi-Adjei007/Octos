from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import BranchListView, BranchViewSet
from .views import ManagerDashboardView

router = DefaultRouter()
router.register(r"branches", BranchViewSet, basename="branch")

app_name = "branches" 

urlpatterns = [
    path("", include(router.urls)),
    path("manager/<int:branch_pk>/dashboard/", ManagerDashboardView.as_view(), name="manager-dashboard"),
    # Branch list (fallback landing for Branch Managers group)
    path("list/", BranchListView.as_view(), name="list"),
]
