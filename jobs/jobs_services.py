# jobs/jobs_services.py

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from jobs.models import Job, JobRecord, DailySale
from branches.models import ServiceType
from django.utils import timezone
from .models import DaySheet
import pytz
from django.db.models import F



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



def _local_date_for_branch(now, branch):
    """
    Return the branch-local date (uses branch.timezone if set, else UTC).
    `now` must be an aware datetime (timezone.now()).
    """
    tzname = getattr(branch, "timezone", None) or "UTC"
    try:
        local = now.astimezone(pytz.timezone(tzname))
    except Exception:
        # fallback to the original aware datetime
        local = now
    return local.date()


def _branch_snapshot(branch):
    """
    Return a dict of snapshot fields from branch for DaySheet population.
    Defensive: handles missing related objects gracefully.
    """
    manager = getattr(branch, "manager", None)
    # attempt to get a full name if manager is an Employee instance
    manager_name = ""
    manager_email = ""
    try:
        if manager:
            # common patterns for Employee naming
            get_full = getattr(manager, "get_full_name", None)
            if callable(get_full):
                manager_name = get_full()
            else:
                # fallback to fields
                manager_name = getattr(manager, "full_name", None) or getattr(manager, "first_name", None) or str(manager)
            manager_email = getattr(manager, "employee_email", None) or getattr(manager, "email", None) or ""
    except Exception:
        manager_name = str(manager) if manager else ""
        manager_email = ""

    branch_city = ""
    try:
        branch_city = getattr(getattr(branch, "city", None), "name", "") or getattr(branch, "branch_city", "") or ""
    except Exception:
        branch_city = ""

    return {
        "branch_name": getattr(branch, "name", "") or "",
        "branch_city": branch_city,
        "branch_manager_name": manager_name or "",
        "branch_manager_email": manager_email or "",
    }


def get_or_create_daysheet_for_branch(branch, user=None, now=None, allow_reopen=False, shift_name=None):
    """
    Return an open DaySheet for the given branch/date or create a new one.
    - Populates snapshot fields (weekday, branch_name, branch_city, branch_manager_*).
    - Uses select_for_update() to avoid race conditions when creating sheets concurrently.
    - Returns (daysheet_instance, created_bool).
    """
    now = now or timezone.now()
    date_local = _local_date_for_branch(now, branch)
    weekday = date_local.strftime("%A")  # e.g., "Wednesday"

    with transaction.atomic():
        # lock and try to get an existing open sheet
        sheet = (
            DaySheet.objects.select_for_update()
            .filter(branch=branch, date=date_local, status=DaySheet.STATUS_OPEN)
            .first()
        )
        if sheet:
            return sheet, False

        # No open sheet; create a new one.
        snap = _branch_snapshot(branch)

        sheet = DaySheet.objects.create(
            branch=branch,
            date=date_local,
            opened_by=user if getattr(user, "is_authenticated", False) else None,
            status=DaySheet.STATUS_OPEN,
            weekday=weekday,
            branch_name=snap["branch_name"],
            branch_city=snap["branch_city"],
            branch_manager_name=snap["branch_manager_name"],
            branch_manager_email=snap["branch_manager_email"],
            shift_name=shift_name or None,
            meta={},  # you can add default meta here if desired
        )
        return sheet, True


# Helper to infer payment type from job
def _infer_payment_type_from_job(job):
    """
    Defensive detection of payment type.
    Priority:
      1. job.payment_type attribute (recommended)
      2. job.meta.get('payment_type')
      3. if deposit_amount == total -> treat as 'deposit' (fallback)
      4. else 'unknown'
    Returns lowercase string: 'cash', 'momo', 'card', 'deposit', 'credit', or 'unknown'
    """
    # direct attribute
    pt = None
    try:
        pt = getattr(job, "payment_type", None)
    except Exception:
        pt = None

    if not pt:
        try:
            meta = getattr(job, "meta", {}) or {}
            pt = meta.get("payment_type")
        except Exception:
            pt = None

    if isinstance(pt, str):
        return pt.lower()

    # fallback heuristics
    try:
        deposit = Decimal(getattr(job, "deposit_amount", 0) or 0)
        price = Decimal(getattr(job, "price", 0) or 0)
        if deposit and deposit < price:
            return "deposit"
        if deposit and deposit == price:
            return "deposit"
    except Exception:
        pass

    return "unknown"


# Idempotent attach of Job to DaySheet
def attach_job_to_daysheet_idempotent(job, user=None, daysheet=None, now=None):
    """
    Idempotent attach: will not double-count a job already attached to a DaySheet.
    Returns: (daysheet_instance, created_bool, counted_bool)
      - created_bool: whether a new DaySheet was created
      - counted_bool: True if this call incremented the DaySheet totals (False if already attached)
    """
    if job is None:
        raise ValueError("job is required")

    now = now or timezone.now()

    # Refresh and lock the job row to avoid race conditions between concurrent requests.
    with transaction.atomic():
        job = Job.objects.select_for_update().get(pk=job.pk)

        # Quick idempotency checks:
        # 1) explicit FK on job (daysheet_id)
        if getattr(job, "daysheet_id", None):
            try:
                existing_ds = DaySheet.objects.get(pk=job.daysheet_id)
            except DaySheet.DoesNotExist:
                existing_ds = None
            return existing_ds, False, False  # not created now, not counted now

        # 2) meta flag attached_to_daysheet
        meta = getattr(job, "meta", {}) or {}
        if meta.get("attached_to_daysheet"):
            # we don't have daysheet_id but meta says attached; try to find by job reference if available
            existing_ds = None
            try:
                existing_ds = DaySheet.objects.filter(meta__contains={"job_ref": job.pk}).first()
            except Exception:
                existing_ds = None
            return existing_ds, False, False

        # Not attached yet — ensure a daysheet exists
        if daysheet is None:
            daysheet, created = get_or_create_daysheet_for_branch(job.branch, user=user, now=now)
        else:
            # ensure it's fresh instance
            daysheet = DaySheet.objects.select_for_update().get(pk=daysheet.pk)
            created = False

        # Compute totals safely
        try:
            job_price = Decimal(job.price or 0)
        except Exception:
            job_price = Decimal(0)
        try:
            job_deposit = Decimal(job.deposit_amount or 0)
        except Exception:
            job_deposit = Decimal(0)
        total_for_job = job_price * max(1, int(getattr(job, "quantity", 1)))

        # Infer payment type helper (use your existing helper or inline)
        payment_type = _infer_payment_type_from_job(job) if "_infer_payment_type_from_job" in globals() else "unknown"

        # update DaySheet totals atomically
        DaySheet.objects.filter(pk=daysheet.pk).update(
            total_jobs=F("total_jobs") + 1,
            total_amount=F("total_amount") + total_for_job,
        )

        if payment_type in ("cash", "cashier", "cash_payment"):
            DaySheet.objects.filter(pk=daysheet.pk).update(cash_total=F("cash_total") + total_for_job)
        elif payment_type in ("momo", "mobile_money", "mobile"):
            DaySheet.objects.filter(pk=daysheet.pk).update(momo_total=F("momo_total") + total_for_job)
        elif payment_type in ("card", "pos", "card_payment"):
            DaySheet.objects.filter(pk=daysheet.pk).update(card_total=F("card_total") + total_for_job)
        elif payment_type == "deposit":
            DaySheet.objects.filter(pk=daysheet.pk).update(deposits_total=F("deposits_total") + job_deposit)
        else:
            # fallback: annotate meta.unclassified_amount (read/modify/write inside transaction)
            ds = DaySheet.objects.select_for_update().get(pk=daysheet.pk)
            ds_meta = ds.meta or {}
            ds_meta_un = ds_meta.get("unclassified_amount", 0) or 0
            try:
                ds_meta["unclassified_amount"] = float(ds_meta_un) + float(total_for_job)
            except Exception:
                ds_meta["unclassified_amount"] = float(total_for_job)
            ds.meta = ds_meta
            ds.save(update_fields=["meta"])

        # Attach job -> daysheet and mark meta flag on job to prevent re-attach
        attached_flag_set = False
        try:
            # prefer fk if model has it
            if hasattr(job, "daysheet_id"):
                job.daysheet_id = daysheet.pk
            else:
                setattr(job, "daysheet", daysheet)
            # set meta flag
            meta = getattr(job, "meta", {}) or {}
            meta["attached_to_daysheet"] = True
            job.meta = meta

            # save only the fields we changed if possible
            save_fields = []
            if "daysheet" in [f.name for f in job._meta.fields]:
                save_fields.append("daysheet")
            if "meta" in [f.name for f in job._meta.fields]:
                save_fields.append("meta")

            if save_fields:
                job.save(update_fields=save_fields)
            else:
                job.save()
            attached_flag_set = True
        except Exception:
            # best-effort: job attach failing shouldn't break totals increment; log in prod
            attached_flag_set = False

        # refresh daysheet for return
        try:
            daysheet.refresh_from_db()
        except Exception:
            pass

        return daysheet, created, True  # counted=True



def get_user_branches(user) -> list:
    # return list of dicts: [{'id': 1, 'name': 'Farhat Westland'}, ...]
    ...

def get_branch_queue_summary(branch_id, limit=20) -> list:
    # return list of job summary dicts: [{'id': 12, 'customer_name': 'Kwesi', 'eta': '2025-11-28T20:00:00Z', 'status':'queued'}, ...]
    ...
