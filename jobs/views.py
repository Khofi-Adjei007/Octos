# re-export API viewsets and include a simple receipt view as fallback
from django.shortcuts import render, get_object_or_404
from jobs.models import Job
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

# import the service layer you created
from .jobs_services import (
    user_is_attendant,
    get_user_branches,
    get_branch_queue_summary,
)


# If API viewsets live in jobs.api.views, re-export them for backward compatibility
try:
    from jobs.api.views import JobViewSet, JobRecordViewSet, JobAttachmentViewSet, job_receipt as api_job_receipt
except Exception:
    JobViewSet = None
    JobRecordViewSet = None
    JobAttachmentViewSet = None
    api_job_receipt = None

def job_receipt(request, job_id):
    # prefer API-provided view if present
    if api_job_receipt:
        return api_job_receipt(request, job_id)
    job = get_object_or_404(Job, pk=job_id)
    return render(request, "jobs/receipt.html", {"job": job})

__all__ = ["JobViewSet", "JobRecordViewSet", "JobAttachmentViewSet", "job_receipt"]


from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.apps import apps

# compatibility facade helpers (delegates to class-based services)
from .jobs_services import user_is_attendant, get_user_branches, get_branch_queue_summary

@login_required
def attendant_dashboard(request):
    """
    Renders the attendant dashboard.
    Normalizes branches and services into simple dicts for templates/JS.
    """
    user = request.user

    # permission check
    if not user_is_attendant(user):
        return HttpResponseForbidden("You are not permitted to access the attendant dashboard.")

    # get branches this attendant can operate at (may be list of dicts or model instances)
    raw_branches = get_user_branches(user) or []

    # normalize branches => list of {'id': .., 'name': ..}
    branches = []
    for b in raw_branches:
        if isinstance(b, dict):
            branches.append({"id": b.get("id"), "name": b.get("name")})
        else:
            branches.append({"id": getattr(b, "pk", getattr(b, "id", None)), "name": getattr(b, "name", str(b))})

    # branch selection via ?branch=ID
    branch_param = request.GET.get("branch")
    active_branch = None
    if branch_param:
        try:
            branch_id = int(branch_param)
            active_branch = next((br for br in branches if br["id"] == branch_id), None)
        except Exception:
            active_branch = None

    # default to first branch if none chosen
    if not active_branch and branches:
        active_branch = branches[0]

    # fetch queue summary for selected branch (list of dicts)
    queue = []
    if active_branch:
        try:
            queue = get_branch_queue_summary(active_branch["id"]) or []
        except Exception:
            queue = []

    # load ServiceType model and normalize service list for the modal
    ServiceType = apps.get_model("branches", "ServiceType")
    services = []
    try:
        qs = ServiceType.objects.all()
        for s in qs:
            meta = getattr(s, "meta", {}) or {}
            # prefer explicit price, then meta.avg_price, then 0
            price = getattr(s, "price", None)
            if price is None:
                price = meta.get("avg_price") or getattr(s, "avg_price", 0)
            services.append({
                "id": getattr(s, "pk", getattr(s, "id", None)),
                "name": getattr(s, "name", getattr(s, "title", "Service")),
                "price": price or 0,
                "meta": meta,
            })
    except Exception:
        services = []

    # messages placeholder (replace with real messaging in future)
    messages = []

    context = {
        "user": user,
        "branches": branches,
        "active_branch": active_branch,
        "queue": queue,
        "services": services,
        "messages": messages,
    }

    return render(request, "attendant/attendant_dashboard.html", context)

