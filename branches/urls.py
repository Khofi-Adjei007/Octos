from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import BranchListView, BranchViewSet
from .views import ManagerDashboardView

# branches/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    BranchListView,
    BranchViewSet,
    branch_manager_dashboard,
    daysheet_new,
    daysheet_close,
    daysheet_lock,
    close_shift,
)
router = DefaultRouter()
router.register(r"branches", BranchViewSet, basename="branch")
router = DefaultRouter()
app_name = "branches"




urlpatterns = [
    path("", include(router.urls)),
    path("manager/<int:branch_pk>/dashboard/", ManagerDashboardView.as_view(), name="manager-dashboard"),
    # Branch list (fallback landing for Branch Managers group)
    path("list/", BranchListView.as_view(), name="list"),

    # API router for BranchViewSet
    path("", include(router.urls)),

    # Rendered manager dashboard (kept for backward compatibility)
    path("manager/<int:branch_id>/dashboard/", branch_manager_dashboard, name="manager-dashboard"),

    # UI-friendly endpoints (match the JS in the dashboard template)
    path("branches/<int:branch_id>/daysheet/new/", daysheet_new, name="daysheet-new"),
    path("branches/<int:branch_id>/daysheet/close/", daysheet_close, name="daysheet-close"),
    path("branches/<int:branch_id>/daysheet/lock/", daysheet_lock, name="daysheet-lock"),
    path("branches/<int:branch_id>/shifts/<int:shift_id>/close/", close_shift, name="shift-close"),

    # Branch list (fallback landing for Branch Managers group)
    path("list/", BranchListView.as_view(), name="list"),
]
