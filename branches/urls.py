from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    BranchListView,
    BranchViewSet,
    branch_manager_dashboard,
    daysheet_new,
    daysheet_close,
    daysheet_lock,
    close_shift,
)

app_name = "branches"

# -------------------------
# API Router
# -------------------------
router = DefaultRouter()
router.register(r"branches", BranchViewSet, basename="branch")

# -------------------------
# URL patterns
# -------------------------
urlpatterns = [
    # API
    path("", include(router.urls)),

    # Manager dashboard (SINGLE canonical route)
    path(
        "manager/<int:branch_pk>/dashboard/",
        branch_manager_dashboard,
        name="manager-dashboard",
    ),

    # Branch list (fallback landing)
    path("list/", BranchListView.as_view(), name="list"),

    # DaySheet actions
    path(
        "branches/<int:branch_id>/daysheet/new/",
        daysheet_new,
        name="daysheet-new",
    ),
    path(
        "branches/<int:branch_id>/daysheet/close/",
        daysheet_close,
        name="daysheet-close",
    ),
    path(
        "branches/<int:branch_id>/daysheet/lock/",
        daysheet_lock,
        name="daysheet-lock",
    ),

    # Shift actions
    path(
        "branches/<int:branch_id>/shifts/<int:shift_id>/close/",
        close_shift,
        name="shift-close",
    ),
]
