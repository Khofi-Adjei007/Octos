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

# attempt to import API viewsets
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




@login_required
def attendant_dashboard(request):
    """
    Renders the attendant dashboard. Attendants are always pinned to a single branch.
    The branch is inferred from the user (employee.branch, user.branch) or fallback.
    """
    user = request.user

    # permission check
    if not user_is_attendant(user):
        return HttpResponseForbidden("You are not permitted to access the attendant dashboard.")

    # try to infer assigned branch (object or dict with id/name)
    assigned_branch_obj = None
    try:
        emp = getattr(user, "employee", None)
        if emp and getattr(emp, "branch", None):
            assigned_branch_obj = emp.branch
    except Exception:
        assigned_branch_obj = None

    if not assigned_branch_obj:
        # try direct attribute
        try:
            if getattr(user, "branch", None):
                assigned_branch_obj = user.branch
        except Exception:
            assigned_branch_obj = None

    # for template convenience build a lightweight dict for active_branch
    active_branch = None
    if assigned_branch_obj:
        active_branch = {"id": getattr(assigned_branch_obj, "pk", getattr(assigned_branch_obj, "id", None)),
                         "name": getattr(assigned_branch_obj, "name", str(assigned_branch_obj))}
    else:
        # fallback to facade that returns available branches as dicts
        branches_list = get_user_branches(user) or []
        if branches_list:
            active_branch = branches_list[0]

    # provide 'branches' for compatibility (but attendants cannot switch in UI)
    branches = []
    try:
        branches = get_user_branches(user) or []
    except Exception:
        branches = []

    # queue for the active branch
    queue = []
    if active_branch and active_branch.get("id"):
        try:
            queue = get_branch_queue_summary(active_branch["id"])
        except Exception:
            queue = []

    context = {
        "user": user,
        "branches": branches,
        "active_branch": active_branch,
        "queue": queue,
    }
    return render(request, "attendant/attendant_dashboard.html", context)
