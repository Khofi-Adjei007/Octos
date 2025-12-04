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

