# re-export API viewsets and include a simple receipt view as fallback
from django.shortcuts import render, get_object_or_404
from jobs.models import Job
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from employees.auth.guards import require_employee_login, require_permission
from django.core.exceptions import PermissionDenied

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




@require_employee_login
@require_permission("record_job")
def attendant_dashboard(request):
    """
    Renders the attendant dashboard.

    Guarded by:
    - active employee
    - record_job permission
    Branch scope is enforced below.
    """

    user = request.user

    # --------------------------------------------------
    # Resolve assigned branch (authoritative)
    # --------------------------------------------------
    assigned_branch_obj = getattr(user, "branch", None)

    if not assigned_branch_obj:
        # Fallback to branch service resolution
        branches = get_user_branches(user) or []
        if not branches:
            raise PermissionDenied("No branch assigned for attendant access.")

        active_branch = branches[0]
    else:
        active_branch = {
            "id": assigned_branch_obj.pk,
            "name": assigned_branch_obj.name,
        }

    # --------------------------------------------------
    # Queue (branch-safe)
    # --------------------------------------------------
    queue = []
    try:
        queue = get_branch_queue_summary(active_branch["id"])
    except Exception:
        queue = []

    context = {
        "user": user,
        "branches": [active_branch],  # attendants cannot switch branches
        "active_branch": active_branch,
        "queue": queue,
    }

    return render(
        request,
        "attendant/attendant_dashboard.html",
        context,
    )

