from celery import shared_task
from django.utils import timezone
from .models import Job
from django.core.mail import send_mail

@shared_task
def send_job_alerts():
    # find jobs nearing ready in next 10 minutes and not already ready/completed
    window = timezone.now() + timezone.timedelta(minutes=10)
    candidates = Job.objects.filter(status__in=["queued","in_progress"], expected_ready_at__lte=window, expected_ready_at__gte=timezone.now())
    for job in candidates:
        # Example: send an email to branch manager (requires branch.manager.email)
        manager = getattr(job.branch, "manager", None)
        if manager and getattr(manager, "email", None):
            send_mail(
                subject=f"Job nearing completion: Job#{job.id}",
                message=f"Job {job.id} for {job.customer_name} is expected at {job.expected_ready_at}.",
                from_email="no-reply@farhat.local",
                recipient_list=[manager.email],
                fail_silently=True,
            )
