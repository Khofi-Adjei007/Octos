from django.utils import timezone
from datetime import timedelta

def compute_queue_position_and_eta(job):
    """
    Simple algorithm:
    - Count number of pending jobs at the branch for same service with status=queued or in_progress created before this job.
    - Compute estimated minutes per unit (job.estimated_total_minutes())
    - ETA = now + sum(estimated minutes of preceding jobs) + this_job_estimate
    Returns (queue_position:int, eta:datetime)
    """
    # count earlier queued jobs for same branch & service
    qs = job.__class__.objects.filter(
        branch=job.branch,
        service=job.service,
        status__in=["queued", "in_progress"]
    ).exclude(pk=job.pk).order_by("created_at")

    # only consider jobs created before this job for queue pos consistency
    earlier = [j for j in qs if j.created_at <= job.created_at]
    queue_position = len(earlier) + 1

    # sum minutes of earlier jobs
    total_minutes = 0
    for j in earlier:
        total_minutes += j.estimated_total_minutes()

    total_minutes += job.estimated_total_minutes()
    eta = timezone.now() + timedelta(minutes=total_minutes)
    return queue_position, eta
