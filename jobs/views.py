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


@login_required
def attendant_dashboard(request):
    """
    Renders the attendant dashboard.
    Keep logic in jobs_services.py: permission checks, branch/query lookups, etc.
    """
    user = request.user

    # permission check (implement in jobs_services.py)
    if not user_is_attendant(user):
        return HttpResponseForbidden("You are not permitted to access the attendant dashboard.")

    # get branches this attendant can operate at (list of dicts)
    branches = get_user_branches(user)  # expected: [{'id':1,'name':'FPP-WEST'}, ...]

    # optional: allow branch selection via query param ?branch=ID
    branch_id = request.GET.get("branch")
    active_branch = None
    if branch_id:
        try:
            branch_id = int(branch_id)
            active_branch = next((b for b in branches if b["id"] == branch_id), None)
        except Exception:
            active_branch = None

    # fetch queue summary for the selected branch (or first branch)
    branch_for_queue = active_branch or (branches[0] if branches else None)
    queue = []
    if branch_for_queue:
        queue = get_branch_queue_summary(branch_for_queue["id"])  # expected: list of job summaries

    context = {
        "user": user,
        "branches": branches,
        "active_branch": branch_for_queue,
        "queue": queue,
    }
    return render(request, "attendant/attendant_dashboard.html", context)

