# ===================================================================
# branches/views.py
# ===================================================================

# -------------------------------------------------------------------
# Standard library
# -------------------------------------------------------------------
import logging
from datetime import time

# -------------------------------------------------------------------
# Django
# -------------------------------------------------------------------
from django.apps import apps
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

# -------------------------------------------------------------------
# Django REST Framework
# -------------------------------------------------------------------
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

# -------------------------------------------------------------------
# Local app imports
# -------------------------------------------------------------------
from .models import Branch
from .api.serializers import BranchBriefSerializer, BranchDetailSerializer
from .api.permissions import IsSuperuserOrReadOnly, IsBranchManagerOrSuperuser
from .api.filters import BranchFilter

# -------------------------------------------------------------------
# New auth system (authoritative)
# -------------------------------------------------------------------
from employees.auth.guards import (
    require_employee_login,
    require_permission,
    require_branch_access,
)

# -------------------------------------------------------------------
# Services
# -------------------------------------------------------------------
from jobs.services import (
    daysheet_service,
    branch_service,
    job_service,
    manager_service,
    shift_service,
    anomaly_service,
    ShiftAggregationService,
)
from employees.auth.guards import (
    require_employee_login,
    require_permission_any,
)
from django.core.exceptions import PermissionDenied


logger = logging.getLogger(__name__)

# ===================================================================
# API LAYER
# ===================================================================

class BranchViewSet(viewsets.ModelViewSet):
    """
    Branch API:
    - list: /api/branches/?brief=true
    - retrieve: /api/branches/{pk}/
    - create: superuser only
    - update/partial_update: branch manager or superuser
    """

    queryset = (
        Branch.objects
        .select_related("country", "region", "city", "district", "location", "manager")
        .prefetch_related("services")
        .all()
    )

    permission_classes = [IsSuperuserOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BranchFilter
    search_fields = ["name", "code", "contact_person", "phone", "email"]
    ordering_fields = ["name", "code", "created_at", "distance_from_main_km"]
    ordering = ["name"]

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            self.permission_classes = [IsBranchManagerOrSuperuser]
        return super().get_permissions()

    def get_serializer_class(self):
        brief = self.request.query_params.get("brief", "false").lower() in ("1", "true", "yes")
        if self.action == "list" and brief:
            return BranchBriefSerializer
        return BranchDetailSerializer

    @action(detail=False, methods=["get"], url_path="nearby")
    def nearby(self, request):
        """
        Return branches within radius_km of lat/lng.
        """
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius_km = float(request.query_params.get("radius_km", 10))

        if not lat or not lng:
            return Response({"detail": "Provide lat and lng"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return Response({"detail": "Invalid lat/lng"}, status=status.HTTP_400_BAD_REQUEST)

        from math import radians, cos, sin, asin, sqrt

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371.0
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            return R * c

        matches = []
        for b in self.get_queryset().filter(is_active=True):
            if b.latitude is None or b.longitude is None:
                continue
            d = haversine(lat, lng, b.latitude, b.longitude)
            if d <= radius_km:
                matches.append((d, b))

        matches.sort(key=lambda x: x[0])
        branches = [m[1] for m in matches]

        serializer = BranchBriefSerializer(branches, many=True, context={"request": request})

        return Response({
            "count": len(branches),
            "radius_km": radius_km,
            "results": serializer.data,
            "distances_km": [round(m[0], 2) for m in matches],
        })

# ===================================================================
# INTERNAL HELPERS (NO AUTH LOGIC)
# ===================================================================

def _get_models():
    DaySheet = apps.get_model("jobs", "DaySheet")
    ShadowLogEvent = apps.get_model("jobs", "ShadowLogEvent")
    DaySheetShift = apps.get_model("jobs", "DaySheetShift")
    return DaySheet, ShadowLogEvent, DaySheetShift

# ===================================================================
# TEMPLATE VIEWS
# ===================================================================

class BranchListView(LoginRequiredMixin, ListView):
    model = Branch
    template_name = "branches/branch_list.html"
    context_object_name = "branches"
    paginate_by = 25

    def get_queryset(self):
        return Branch.objects.filter(is_active=True).order_by("name")

# ===================================================================
# BRANCH MANAGER DASHBOARD
# ===================================================================

# ===================================================================
# BRANCH MANAGER DASHBOARD
# ===================================================================

@require_employee_login
@require_permission_any(
    ("manage_branch", "close_day", "view_branch_reports")
)
@require_branch_access(
    lambda request, *a, **kw: kw.get("branch_pk") or request.employee_context.branch_id
)
def branch_manager_dashboard(request, branch_pk=None):
    """
    Branch Manager Dashboard

    Access rules:
    - active employee
    - at least one manager-level permission
    - authority over the requested branch
    """

    Branch = apps.get_model("branches", "Branch")
    DaySheet, ShadowLogEvent, DaySheetShift = _get_models()

    # -------------------------------------------------
    # Resolve manager branch authority
    # -------------------------------------------------
    branches = branch_service.get_user_branches(request.user) or []

    if not branches:
        raise PermissionDenied("No branch assigned for manager access.")

    # Requested branch
    if branch_pk is not None:
        try:
            branch_id = int(branch_pk)
        except (TypeError, ValueError):
            raise PermissionDenied("Invalid branch identifier.")

        active_branch = next(
            (b for b in branches if b["id"] == branch_id),
            None,
        )

        if not active_branch:
            raise PermissionDenied("You are not authorized for this branch.")

    # Default branch (single or first)
    else:
        active_branch = branches[0]

    branch_obj = get_object_or_404(Branch, pk=active_branch["id"])

    # -------------------------------------------------
    # Business logic (UNCHANGED)
    # -------------------------------------------------
    aggregator = ShiftAggregationService()

    def _within_day_close_window(now=None):
        now = now or timezone.localtime()
        return time(19, 30) <= now.time() <= time(20, 30)

    # -------------------------------------------------
    # Today’s DaySheet
    # -------------------------------------------------
    try:
        todays_sheet_obj, _ = daysheet_service.get_or_create_daysheet_for_branch(
            branch_obj,
            user=request.user,
            now=timezone.now(),
        )
    except Exception:
        todays_sheet_obj = DaySheet.objects.filter(
            branch=branch_obj,
            date=timezone.localdate(),
        ).first()

    todays_sheet = {
        "total_jobs": getattr(todays_sheet_obj, "total_jobs", 0),
        "total_amount": getattr(todays_sheet_obj, "total_amount", 0),
        "pending_amount": (
            todays_sheet_obj.meta.get("pending_amount", 0)
            if getattr(todays_sheet_obj, "meta", None)
            else 0
        ),
        "jobs_change_pct": (
            todays_sheet_obj.meta.get("jobs_change_pct", 0)
            if getattr(todays_sheet_obj, "meta", None)
            else 0
        ),
        "date": getattr(todays_sheet_obj, "date", None),
    }

    # -------------------------------------------------
    # Queue
    # -------------------------------------------------
    queue_items = branch_service.get_branch_queue_summary(branch_obj.pk) or []
    queue_count = len(queue_items)

    # -------------------------------------------------
    # Shifts
    # -------------------------------------------------
    recent_shifts = []

    if todays_sheet_obj:
        shifts = (
            DaySheetShift.objects
            .filter(daysheet=todays_sheet_obj)
            .select_related("user")
            .order_by("shift_start")
        )

        for shift in shifts:
            try:
                agg = aggregator.aggregate(shift)
            except Exception:
                continue

            user = shift.user
            user_name = (
                user.get_full_name()
                if user and hasattr(user, "get_full_name")
                else str(user)
            )

            recent_shifts.append({
                "id": shift.pk,
                "user_name": user_name,
                "shift_start": shift.shift_start,
                "shift_end": shift.shift_end,
                "deposit_total": agg["deposit_total"],
                "collected_total": agg["net_total"],
                "status": shift.status,
                "can_close": (
                    shift.status == DaySheetShift.SHIFT_OPEN
                    and _within_day_close_window()
                ),
            })

    # -------------------------------------------------
    # Activity / messages
    # -------------------------------------------------
    recent_messages = []

    try:
        events = (
            ShadowLogEvent.objects
            .filter(branch_id=branch_obj.pk)
            .order_by("-timestamp")[:10]
        )

        for ev in events:
            recent_messages.append({
                "title": ev.event_type.replace("_", " ").title(),
                "created_at": ev.timestamp,
            })
    except Exception:
        pass

    # -------------------------------------------------
    # Render
    # -------------------------------------------------
    context = {
        "branch": branch_obj,
        "branch_display": branch_obj.name,
        "profile_picture_url": getattr(request.user, "profile_picture_url", "") or "",
        "logout_url": getattr(request, "logout_url", "/accounts/logout/"),
        "quick_record_url": f"/branches/{branch_obj.pk}/jobs/new/",
        "manager_dashboard_url": request.path,
        "todays_sheet": todays_sheet,
        "todays_sheet_obj": todays_sheet_obj,
        "recent_shifts": recent_shifts,
        "queue_items": queue_items,
        "queue_count": queue_count,
        "recent_messages": recent_messages,
    }

    return render(
        request,
        "branches/manager/branch_manager_dashboard.html",
        context,
    )


# ===================================================================
# MANAGER ACTIONS (POST)
# ===================================================================

@require_employee_login
@require_permission("manage_branch")
@require_branch_access(lambda r, *a, **kw: kw["branch_id"])
@require_POST
def daysheet_new(request, branch_id):
    Branch = apps.get_model("branches", "Branch")
    branch = get_object_or_404(Branch, pk=branch_id)

    sheet, created = daysheet_service.get_or_create_daysheet_for_branch(
        branch, user=request.user, now=timezone.now()
    )

    return JsonResponse({
        "ok": True,
        "created": created,
        "daysheet_id": sheet.pk,
    })


@require_employee_login
@require_permission("manage_branch")
@require_branch_access(lambda r, *a, **kw: kw["branch_id"])
@require_POST
def daysheet_close(request, branch_id):
    Branch = apps.get_model("branches", "Branch")
    DaySheet = apps.get_model("jobs", "DaySheet")

    branch = get_object_or_404(Branch, pk=branch_id)
    today = timezone.localdate()

    sheet = DaySheet.objects.filter(branch=branch, date=today).first()
    if not sheet:
        return JsonResponse({"ok": False, "detail": "No daysheet"}, status=400)

    try:
        manager_service.manager_close_day(sheet, request.user, now=timezone.now())
        return JsonResponse({"ok": True})
    except PermissionDenied as exc:
        return JsonResponse({"ok": False, "detail": str(exc)}, status=403)


@require_employee_login
@require_permission("manage_branch")
@require_branch_access(lambda r, *a, **kw: kw["branch_id"])
@require_POST
def daysheet_lock(request, branch_id):
    DaySheet = apps.get_model("jobs", "DaySheet")
    today = timezone.localdate()

    sheet = DaySheet.objects.filter(branch_id=branch_id, date=today).first()
    if not sheet:
        return JsonResponse({"ok": False, "detail": "No daysheet"}, status=400)

    sheet.locked = not sheet.locked
    sheet.save(update_fields=["locked"])

    return JsonResponse({"ok": True, "locked": sheet.locked})


@require_employee_login
@require_permission("manage_branch")
@require_branch_access(lambda r, *a, **kw: kw["branch_id"])
@require_POST
def close_shift(request, branch_id, shift_id):
    DaySheetShift = apps.get_model("jobs", "DaySheetShift")

    shift = DaySheetShift.objects.filter(
        pk=shift_id,
        daysheet__branch_id=branch_id,
    ).first()

    if not shift:
        return JsonResponse({"ok": False, "detail": "Shift not found"}, status=404)

    try:
        shift_service.close_shift(
            shift,
            request.user,
            now=timezone.now(),
        )
        return JsonResponse({"ok": True})
    except PermissionDenied as exc:
        return JsonResponse({"ok": False, "detail": str(exc)}, status=403)
