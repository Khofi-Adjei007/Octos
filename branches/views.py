from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Branch
from .api.serializers import BranchBriefSerializer, BranchDetailSerializer
from .api.permissions import IsSuperuserOrReadOnly, IsBranchManagerOrSuperuser
from .api.filters import BranchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from .permissions import is_branch_manager
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, NoReverseMatch

class BranchViewSet(viewsets.ModelViewSet):
    """
    Branch API:
    - list: /api/branches/?brief=true
    - retrieve: /api/branches/{pk}/
    - create: CEO/superuser only
    - partial_update: branch manager or superuser
    """
    queryset = Branch.objects.select_related("country", "region", "city", "district", "location", "manager").prefetch_related("services").all()
    permission_classes = [IsSuperuserOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BranchFilter
    search_fields = ["name", "code", "contact_person", "phone", "email"]
    ordering_fields = ["name", "code", "created_at", "distance_from_main_km"]
    ordering = ["name"]

    def get_permissions(self):
        # use object-level permission for unsafe object updates
        if self.action in ("partial_update", "update", "destroy"):
            self.permission_classes = [IsBranchManagerOrSuperuser]
        else:
            self.permission_classes = [IsSuperuserOrReadOnly]
        return super().get_permissions()

    def get_serializer_class(self):
        # allow a compact serializer for brief list use
        brief = self.request.query_params.get("brief", "false").lower() in ("1", "true", "yes")
        if self.action == "list" and brief:
            return BranchBriefSerializer
        if self.action in ("create", "update", "partial_update"):
            return BranchDetailSerializer
        # for retrieve and default list, use detail serializer
        return BranchDetailSerializer

    def perform_create(self, serializer):
        # if you want to capture created_by, add here (requires Branch to have created_by)
        serializer.save()

    @action(detail=False, methods=["get"], url_path="nearby")
    def nearby(self, request):
        """
        Optional helper: return branches within radius_km of lat/lng.
        Usage: /api/branches/nearby/?lat=5.6&lng=-0.2&radius_km=10
        This implementation does a simple Haversine filter in Python and is fine for small datasets.
        For heavy usage, use PostGIS.
        """
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius_km = float(request.query_params.get("radius_km", 10))
        if not lat or not lng:
            return Response({"detail": "Provide lat and lng query params"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lat = float(lat); lng = float(lng)
        except ValueError:
            return Response({"detail": "Invalid lat/lng"}, status=status.HTTP_400_BAD_REQUEST)

        # cheap filter: compute distance in DB-unsafe way (could be optimized)
        from math import radians, cos, sin, asin, sqrt
        def haversine(lat1, lon1, lat2, lon2):
            # returns km
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

        # sort by distance and serialize
        matches.sort(key=lambda x: x[0])
        branches = [m[1] for m in matches]
        serializer = BranchBriefSerializer(branches, many=True, context={"request": request})
        # include distances as parallel list
        return Response({
            "count": len(branches),
            "radius_km": radius_km,
            "results": serializer.data,
            "distances_km": [round(m[0], 2) for m in matches]
        })


class BranchManagerRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        # Expect branch_pk as URL kwarg
        branch_pk = kwargs.get('branch_pk') or request.GET.get('branch_pk')
        if not branch_pk:
            raise PermissionDenied("Branch not specified")
        branch = get_object_or_404(Branch, pk=branch_pk)
        if not is_branch_manager(request.user, branch):
            raise PermissionDenied("You are not the manager for this branch")
        # attach branch for convenience
        request.branch = branch
        return super().dispatch(request, *args, **kwargs)

from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class ManagerDashboardView(BranchManagerRequiredMixin, TemplateView):
    template_name = "branches/manager/branch_manager_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        branch = getattr(self.request, "branch", None)

        # safe defaults
        todays_sheet = {
            "total_jobs": 0,
            "total_amount": "0.00",
            "pending_amount": "0.00",
            "jobs_change_pct": "0",
        }
        queue_items = []
        queue_count = 0
        recent_messages = []

        today = timezone.localdate()

        # Helper to lookup a related manager by common attribute names
        def find_related_manager(obj, candidates):
            for name in candidates:
                mgr = getattr(obj, name, None)
                if mgr is not None:
                    return mgr
            return None

        if branch is not None:
            # 1) Try to find a daysheet related manager on the branch
            daysheet_manager = find_related_manager(branch, [
                "daysheet_set", "daily_sheet_set", "daysheets", "daily_sheets", "sheet_set"
            ])

            if daysheet_manager is not None:
                try:
                    # prefer filter by date field named 'date' or 'day' or 'created_at'
                    sheet_qs = None
                    for date_field in ("date", "day", "created_at"):
                        try:
                            sheet_qs = daysheet_manager.filter(**{date_field: today})
                            if sheet_qs.exists():
                                break
                        except Exception:
                            sheet_qs = None
                    # fallback to .first() on manager if the above didn't work
                    sheet = None
                    if sheet_qs:
                        sheet = sheet_qs.first()
                    else:
                        try:
                            sheet = daysheet_manager.first()
                        except Exception:
                            sheet = None

                    if sheet:
                        # attempt to read common attrs; fall back to dict access
                        def _get(o, *names, default=None):
                            for n in names:
                                try:
                                    val = getattr(o, n)
                                    if val is not None:
                                        return val
                                except Exception:
                                    # try dict-like access
                                    try:
                                        return o[n]
                                    except Exception:
                                        pass
                            return default

                        todays_sheet = {
                            "total_jobs": _get(sheet, "total_jobs", "jobs_count", "num_jobs", default=0) or 0,
                            "total_amount": _get(sheet, "total_amount", "amount_total", "gross", default="0.00") or "0.00",
                            "pending_amount": _get(sheet, "pending_amount", "amount_pending", default="0.00") or "0.00",
                            "jobs_change_pct": _get(sheet, "jobs_change_pct", "change_pct", default="0") or "0",
                        }
                except Exception as exc:
                    logger.debug("Error resolving daysheet for branch %s: %s", getattr(branch, "pk", None), exc)
            else:
                logger.debug("No daysheet relation found on Branch(pk=%s). Tried common names.", getattr(branch, "pk", None))

            # 2) Try to find jobs/queue related manager on the branch
            jobs_manager = find_related_manager(branch, [
                "jobs", "job_set", "jobs_set", "branch_jobs", "queue", "order_set", "orders"
            ])
            if jobs_manager is not None:
                try:
                    # get open jobs (common status names)
                    open_qs = None
                    try:
                        open_qs = jobs_manager.filter(status__in=["OPEN", "PENDING", "QUEUE"])
                    except Exception:
                        open_qs = jobs_manager.all()
                    items = list(open_qs.order_by("-pk")[:20]) if hasattr(open_qs, "order_by") else list(open_qs)[:20]

                    def job_to_dict(j):
                        return {
                            "id": getattr(j, "pk", None) or getattr(j, "id", None),
                            "customer_name": getattr(j, "customer_name", None) or getattr(j, "customer", None) or getattr(j, "customer_phone", None) or "",
                            "customer_phone": getattr(j, "customer_phone", None),
                            "service_name": getattr(j, "service_name", None) or getattr(j, "service", None) or "",
                            "quantity": getattr(j, "quantity", None) or getattr(j, "qty", None) or 1,
                            "total_amount": getattr(j, "total_amount", None) or getattr(j, "amount", None) or "0.00",
                            "status": getattr(j, "status", None) or "OPEN",
                        }
                    queue_items = [job_to_dict(j) for j in items]
                    # compute queue_count safely
                    try:
                        if hasattr(open_qs, "count"):
                            queue_count = int(open_qs.count())
                        else:
                            queue_count = len(queue_items)
                    except Exception:
                        queue_count = len(queue_items)
                except Exception as exc:
                    logger.debug("Error resolving jobs for branch %s: %s", getattr(branch, "pk", None), exc)
            else:
                logger.debug("No jobs relation found on Branch(pk=%s). Tried common names.", getattr(branch, "pk", None))

            # 3) recent messages / notifications
            messages_manager = find_related_manager(branch, ["messages", "message_set", "notifications", "activity_set", "activities"])
            if messages_manager is not None:
                try:
                    recent_qs = messages_manager.all().order_by("-pk")[:10]
                    recent_messages = []
                    for m in recent_qs:
                        recent_messages.append({
                            "title": getattr(m, "title", None) or getattr(m, "message", None) or str(m),
                            "created_at": getattr(m, "created_at", None) or getattr(m, "timestamp", None) or getattr(m, "date", None),
                        })
                except Exception as exc:
                    logger.debug("Error resolving messages for branch %s: %s", getattr(branch, "pk", None), exc)
            else:
                recent_messages = []

        # safe URL reversals for template usage (avoid NoReverseMatch in template)
        quick_record_url = None
        manager_dashboard_url = "/"
        logout_url = "#"
        try:
            quick_record_url = reverse('jobs:quick_record')
        except NoReverseMatch:
            quick_record_url = None

        try:
            if branch is not None:
                manager_dashboard_url = reverse('branches:manager-dashboard', kwargs={'branch_pk': branch.pk})
            else:
                manager_dashboard_url = reverse('branches:list')
        except NoReverseMatch:
            manager_dashboard_url = "/"

        try:
            # prefer namespaced employees:logout if present
            logout_url = reverse('employees:logout')
        except NoReverseMatch:
            try:
                logout_url = reverse('logout')
            except NoReverseMatch:
                logout_url = "#"

        # Final safe context population
        ctx.update({
            "branch": branch,
            "todays_sheet": todays_sheet,
            "queue_items": queue_items,
            "queue_count": queue_count,
            "recent_messages": recent_messages,
            "quick_record_url": quick_record_url,
            "manager_dashboard_url": manager_dashboard_url,
            "logout_url": logout_url,
        })
        return ctx





class BranchListView(LoginRequiredMixin, ListView):
    model = Branch
    template_name = "branches/branch_list.html"
    context_object_name = "branches"
    paginate_by = 25

    def get_queryset(self):
        # Optionally: restrict non-superusers to active branches only
        qs = Branch.objects.filter(is_active=True).order_by('name')
        return qs


# branches/views.py (add / replace relevant parts)
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.apps import apps
from django.core.exceptions import PermissionDenied
from django.utils import timezone

# services (class-based singletons in jobs.services)
from jobs.services import (
    daysheet_service,
    branch_service,
    job_service,
    manager_service,
    shift_service,
    anomaly_service,
)

def _get_models():
    DaySheet = apps.get_model("jobs", "DaySheet")
    ShadowLogEvent = apps.get_model("jobs", "ShadowLogEvent")
    DaySheetShift = apps.get_model("jobs", "DaySheetShift")
    return DaySheet, ShadowLogEvent, DaySheetShift

def _manager_of_branch(user, branch_obj):
    try:
        return branch_service._is_manager_of_branch(user, branch_obj)
    except Exception:
        try:
            mgr = getattr(branch_obj, "manager", None)
            if mgr is None:
                return False
            if mgr == user or getattr(mgr, "user", None) == user or getattr(mgr, "pk", None) == getattr(user, "pk", None):
                return True
        except Exception:
            return False
    return False

@login_required
def branch_manager_dashboard(request, branch_id=None):
    """
    Render branch manager dashboard and wire Daily Sheets data.
    If branch_id not provided, attempt to find branches managed by user and pick the first.
    """
    Branch = apps.get_model("branches", "Branch")
    DaySheet, ShadowLogEvent, DaySheetShift = _get_models()

    # Determine active branch
    active_branch = None
    branches = branch_service.get_user_branches(request.user) or []
    if branch_id:
        try:
            branch_id_int = int(branch_id)
            active_branch = next((b for b in branches if b["id"] == branch_id_int), None)
            if not active_branch:
                branch_obj = get_object_or_404(Branch, pk=branch_id_int)
                if not _manager_of_branch(request.user, branch_obj):
                    return HttpResponseForbidden("You are not manager of this branch.")
                active_branch = {"id": branch_obj.pk, "name": getattr(branch_obj, "name", str(branch_obj))}
        except Exception:
            active_branch = None
    else:
        active_branch = branches[0] if branches else None

    if not active_branch:
        try:
            if hasattr(request.user, "employee"):
                br = getattr(request.user.employee, "branch", None)
                if br:
                    active_branch = {"id": br.pk, "name": getattr(br, "name", str(br))}
        except Exception:
            pass

    if not active_branch:
        return HttpResponseForbidden("No branch available for you to manage.")

    # get branch model instance
    branch_obj = get_object_or_404(Branch, pk=active_branch["id"])

    if not _manager_of_branch(request.user, branch_obj):
        return HttpResponseForbidden("You must be branch manager to access this page.")

    # get today's sheet (create if missing)
    try:
        todays_sheet_obj, created = daysheet_service.get_or_create_daysheet_for_branch(branch_obj, user=request.user, now=timezone.now())
    except Exception:
        try:
            today = timezone.localdate()
            DaySheet = apps.get_model("jobs", "DaySheet")
            todays_sheet_obj = DaySheet.objects.filter(branch=branch_obj, date=today).first()
            created = False
        except Exception:
            todays_sheet_obj = None
            created = False

    # prepare digest for template
    todays_sheet = {
        "total_jobs": getattr(todays_sheet_obj, "total_jobs", 0),
        "total_amount": getattr(todays_sheet_obj, "total_amount", 0),
        "jobs_change_pct": (todays_sheet_obj.meta.get("jobs_change_pct") if getattr(todays_sheet_obj, "meta", None) else None) or 0,
        "pending_amount": (todays_sheet_obj.meta.get("pending_amount") if getattr(todays_sheet_obj, "meta", None) else None) or 0,
        "date": getattr(todays_sheet_obj, "date", None),
    }

    queue_items = branch_service.get_branch_queue_summary(branch_obj.pk) or []
    queue_count = len(queue_items)

    # recent shifts (simple digest)
    recent_shifts = []
    try:
        DaySheetShift = apps.get_model("jobs", "DaySheetShift")
        shifts = DaySheetShift.objects.filter(daysheet__branch=branch_obj).order_by("-created_at")[:8]
        for s in shifts:
            recent_shifts.append({
                "id": s.pk,
                "user_name": getattr(getattr(s, "user", None), "get_full_name", lambda: str(getattr(s, "user", None)))(),
                "shift_start": getattr(s, "shift_start", None),
                "shift_end": getattr(s, "shift_end", None),
                "status": getattr(s, "status", None),
            })
    except Exception:
        recent_shifts = []

    # recent messages / activity (use ShadowLogEvent)
    recent_messages = []
    try:
        ShadowLogEvent = apps.get_model("jobs", "ShadowLogEvent")
        recent_qs = ShadowLogEvent.objects.filter(branch_id=branch_obj.pk).order_by("-timestamp")[:10]
        for ev in recent_qs:
            recent_messages.append({
                "title": ev.event_type.replace("_", " ").title(),
                "created_at": getattr(ev, "timestamp", None),
            })
    except Exception:
        recent_messages = []

    quick_record_url = f"/branches/{branch_obj.pk}/jobs/new/"
    manager_dashboard_url = request.path
    logout_url = getattr(request, "logout_url", "/accounts/logout/")
    profile_picture_url = getattr(request.user, "profile_picture_url", None) or ""

    context = {
        "branch": branch_obj,
        "branch_display": getattr(branch_obj, "name", str(branch_obj)),
        "profile_picture_url": profile_picture_url,
        "logout_url": logout_url,
        "quick_record_url": quick_record_url,
        "manager_dashboard_url": manager_dashboard_url,
        "todays_sheet": todays_sheet,
        "todays_sheet_obj": todays_sheet_obj,
        "recent_shifts": recent_shifts,
        "queue_items": queue_items,
        "queue_count": queue_count,
        "recent_messages": recent_messages,
    }

    return render(request, "branches/manager/branch_manager_dashboard.html", context)


# -------------------------
# Minimal manager actions (endpoints)
# -------------------------
@login_required
@require_POST
def daysheet_new(request, branch_id):
    """Create a new DaySheet for branch (if none exists today)."""
    Branch = apps.get_model("branches", "Branch")
    branch_obj = get_object_or_404(Branch, pk=branch_id)

    if not _manager_of_branch(request.user, branch_obj):
        return JsonResponse({"ok": False, "detail": "Not allowed"}, status=403)

    try:
        sheet, created = daysheet_service.get_or_create_daysheet_for_branch(branch_obj, user=request.user, now=timezone.now())
        return JsonResponse({"ok": True, "created": created, "daysheet_id": sheet.pk, "date": str(sheet.date)})
    except Exception as e:
        return JsonResponse({"ok": False, "detail": "Could not create daysheet", "error": str(e)}, status=500)


@login_required
@require_POST
def daysheet_close(request, branch_id):
    """
    Manager closes the day's sheet. Expects POST JSON payload: {"pin": "1234"}.
    Returns JSON with success or error message.
    """
    Branch = apps.get_model("branches", "Branch")
    DaySheet = apps.get_model("jobs", "DaySheet")
    branch_obj = get_object_or_404(Branch, pk=branch_id)

    if not _manager_of_branch(request.user, branch_obj):
        return JsonResponse({"ok": False, "detail": "Not allowed"}, status=403)

    # parse JSON safely
    try:
        import json
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        payload = request.POST.dict() if hasattr(request, "POST") else {}

    pin = (payload.get("pin") or "").strip()
    if not pin:
        return JsonResponse({"ok": False, "detail": "PIN is required"}, status=400)

    today = timezone.localdate()
    daysheet = DaySheet.objects.filter(branch=branch_obj, date=today).first()
    if not daysheet:
        return JsonResponse({"ok": False, "detail": "No open daysheet for today"}, status=400)

    try:
        manager_service.manager_close_day(daysheet, request.user, pin=pin, now=timezone.now())
        return JsonResponse({"ok": True, "detail": "Day closed", "daysheet_id": daysheet.pk})
    except PermissionDenied:
        return JsonResponse({"ok": False, "detail": "Invalid PIN"}, status=403)
    except ValueError as ve:
        return JsonResponse({"ok": False, "detail": str(ve)}, status=400)
    except Exception as exc:
        return JsonResponse({"ok": False, "detail": "Failed to close day", "error": str(exc)}, status=500)


@login_required
@require_POST
def daysheet_lock(request, branch_id):
    """
    Lock/open the daysheet (manager action). Accepts POST JSON {'action':'lock'|'unlock'}
    """
    Branch = apps.get_model("branches", "Branch")
    DaySheet = apps.get_model("jobs", "DaySheet")
    branch_obj = get_object_or_404(Branch, pk=branch_id)

    if not _manager_of_branch(request.user, branch_obj):
        return JsonResponse({"ok": False, "detail": "Not allowed"}, status=403)

    try:
        import json
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        payload = request.POST.dict() if hasattr(request, "POST") else {}

    action = payload.get("action")
    if action not in ("lock", "unlock"):
        return JsonResponse({"ok": False, "detail": "Invalid action"}, status=400)

    try:
        today = timezone.localdate()
        daysheet = DaySheet.objects.filter(branch=branch_obj, date=today).first()
        if not daysheet:
            return JsonResponse({"ok": False, "detail": "No daysheet found for today"}, status=400)

        daysheet.locked = (action == "lock")
        daysheet.save(update_fields=["locked"])
        return JsonResponse({"ok": True, "locked": daysheet.locked})
    except Exception as exc:
        return JsonResponse({"ok": False, "detail": "Failed to update lock", "error": str(exc)}, status=500)


@login_required
@require_POST
def close_shift(request, branch_id, shift_id):
    """
    Close an open shift. Expects JSON payload: {'closing_cash': '100.00', 'pin': '1234'}.
    Delegates to shift_service.close_shift.
    """
    Branch = apps.get_model("branches", "Branch")
    DaySheetShift = apps.get_model("jobs", "DaySheetShift")
    branch_obj = get_object_or_404(Branch, pk=branch_id)

    if not _manager_of_branch(request.user, branch_obj):
        return JsonResponse({"ok": False, "detail": "Not allowed"}, status=403)

    try:
        import json
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        payload = request.POST.dict() if hasattr(request, "POST") else {}

    expected_keys = ("closing_cash", "pin")
    if not all(k in payload for k in expected_keys):
        return JsonResponse({"ok": False, "detail": "closing_cash and pin are required"}, status=400)

    shift = DaySheetShift.objects.filter(pk=shift_id, daysheet__branch=branch_obj).first()
    if not shift:
        return JsonResponse({"ok": False, "detail": "Shift not found"}, status=404)

    try:
        closing_cash = payload.get("closing_cash")
        pin = payload.get("pin")
        shift_service.close_shift(shift, request.user, closing_cash=closing_cash, pin=pin, now=timezone.now())
        return JsonResponse({"ok": True, "detail": "Shift closed", "shift_id": shift.pk})
    except PermissionDenied:
        return JsonResponse({"ok": False, "detail": "Invalid PIN"}, status=403)
    except Exception as exc:
        return JsonResponse({"ok": False, "detail": "Failed to close shift", "error": str(exc)}, status=500)
