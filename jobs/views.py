# re-export API viewsets and include a simple receipt view as fallback
from django.shortcuts import render, get_object_or_404
from jobs.models import Job

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
