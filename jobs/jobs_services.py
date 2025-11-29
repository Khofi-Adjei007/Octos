# jobs/jobs_services.py

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from jobs.models import Job, JobRecord, DailySale
from branches.models import ServiceType

def create_instant_job(branch_id, service_id, quantity, created_by=None, customer_name=None, customer_phone=None, deposit=0, description=""):
    svc = ServiceType.objects.get(pk=service_id)
    unit_price = getattr(svc, "price", None) or Decimal("0.00")
    qty = int(quantity or 1)
    deposit = Decimal(deposit or 0)
    total = (Decimal(unit_price) * qty) - deposit
    if total < 0:
        total = Decimal("0.00")

    with transaction.atomic():
        job = Job.objects.create(
            branch_id=branch_id,
            service=svc,
            customer_name=customer_name or "",
            customer_phone=customer_phone or "",
            description=description or "",
            quantity=qty,
            unit_price=unit_price,
            total_amount=total.quantize(Decimal("0.01")),
            deposit_amount=deposit,
            type="instant",
            status="completed",
            completed_at=timezone.now(),
            created_by=created_by
        )

        JobRecord.objects.create(
            job=job,
            performed_by=created_by,
            time_start=timezone.now(),
            time_end=timezone.now(),
            quantity_produced=qty,
            notes="Instant (attendant) job created and completed",
        )

        today = timezone.localdate()
        ds, _ = DailySale.objects.get_or_create(branch_id=branch_id, date=today, defaults={"total_amount":0, "total_count":0})
        ds.total_amount = ds.total_amount + job.total_amount
        ds.total_count = ds.total_count + 1
        ds.save(update_fields=["total_amount", "total_count", "updated_at"])

    return job


def user_is_attendant(user) -> bool:
    """
    Return True if the given user should be considered an attendant.
    Adjust to match where your project stores role info:
      - Employee.role (Employee linked to user)
      - user.role (role directly on user)
      - user.groups / permissions
    """
    try:
        # Prefer Employee -> role relationship
        emp = getattr(user, "employee", None) or getattr(user, "userprofile", None)
        if emp and hasattr(emp, "role") and emp.role:
            return getattr(emp.role, "code", "").upper() == "ATTENDANT"
    except Exception:
        pass

    # fallback: user model has role directly
    try:
        role = getattr(user, "role", None)
        if role and getattr(role, "code", "").upper() == "ATTENDANT":
            return True
    except Exception:
        pass

    # fallback: check group membership
    try:
        if user.groups.filter(name__iexact="attendant").exists():
            return True
    except Exception:
        pass

    return False


def get_user_branches(user) -> list:
    # return list of dicts: [{'id': 1, 'name': 'Farhat Westland'}, ...]
    ...

def get_branch_queue_summary(branch_id, limit=20) -> list:
    # return list of job summary dicts: [{'id': 12, 'customer_name': 'Kwesi', 'eta': '2025-11-28T20:00:00Z', 'status':'queued'}, ...]
    ...
