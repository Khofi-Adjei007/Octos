# jobs/jobs_services.py
"""
Compatibility facade that preserves the original function names by delegating
to the new class-based services implemented in jobs.services.

Keep this module thin — it exists so older code that imports functions from
jobs.jobs_services continues to work while the codebase migrates to the
class-based service API.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional, Tuple, Any, Dict
import warnings

# Import the concrete services (singletons) from the new module.
# If import fails early, surface a clear error.
try:
    from .services import branch_service
    from .services import (
        job_service,
        daysheet_service,
        shift_service,
        manager_service,
        correction_service,
        anomaly_service,
        user_is_attendant_static,
    )
except Exception as exc:
    raise ImportError("Failed to import jobs.services — ensure jobs.services is available and importable.") from exc

# Emit a gentle one-time warning so callers know new service objects exist.
warnings.warn(
    "jobs.jobs_services is a compatibility facade. Prefer using jobs.services.* singletons directly.",
    DeprecationWarning,
    stacklevel=2,
)

# Public API
__all__ = [
    "create_instant_job",
    "attach_job_to_daysheet_idempotent",
    "get_or_create_daysheet_for_branch",
    "start_shift",
    "close_shift",
    "manager_close_day",
    "detect_duplicate_job",
    "detect_high_free_jobs",
    "auto_close_shift_and_flag",
    "auto_close_daysheet_if_needed",
    "user_is_attendant",
    "_infer_payment_type_from_job",
    "get_user_branches",
    "get_branch_queue_summary",
]

# Re-exported functions (delegating)


def create_instant_job(
    branch_id,
    service_id,
    quantity,
    created_by=None,
    customer_name=None,
    customer_phone=None,
    deposit=0,
    description="",
):
    """Create an instant job (delegates to JobService.create_instant_job)."""
    return job_service.create_instant_job(
        branch_id,
        service_id,
        quantity,
        created_by=created_by,
        customer_name=customer_name,
        customer_phone=customer_phone,
        deposit=deposit,
        description=description,
    )


def attach_job_to_daysheet_idempotent(job, user=None, daysheet=None, now=None) -> Tuple:
    """Attach a Job to the day's DaySheet idempotently."""
    return job_service.attach_job_to_daysheet_idempotent(job, user=user, daysheet=daysheet, now=now)


def get_or_create_daysheet_for_branch(branch, user=None, now=None, allow_reopen=False, shift_name=None):
    """Get or create a DaySheet for a branch/date."""
    return daysheet_service.get_or_create_daysheet_for_branch(branch, user=user, now=now, allow_reopen=allow_reopen, shift_name=shift_name)


def start_shift(branch, user, now=None, role: str = "ATTENDANT", shift_name: Optional[str] = None):
    """Start a shift (delegates to ShiftService.start_shift)."""
    return shift_service.start_shift(branch, user, now=now, role=role, shift_name=shift_name)


def close_shift(shift, user, closing_cash: Decimal, pin: str, now=None):
    """Close a shift (delegates to ShiftService.close_shift)."""
    return shift_service.close_shift(shift, user, closing_cash=closing_cash, pin=pin, now=now)


def manager_close_day(daysheet, manager_user, pin: str, now=None):
    """Manager closes a DaySheet (delegates to ManagerService.manager_close_day)."""
    return manager_service.manager_close_day(daysheet, manager_user, pin=pin, now=now)


def detect_duplicate_job(job, window_seconds: int = 120):
    """Detect duplicate job within a short window (delegates to AnomalyService)."""
    return anomaly_service.detect_duplicate_job(job, window_seconds=window_seconds)


def detect_high_free_jobs(daysheet, free_ratio_threshold: float = 0.2):
    """Detect unusually high ratio of non-priced/free services in a DaySheet."""
    return anomaly_service.detect_high_free_jobs(daysheet, free_ratio_threshold=free_ratio_threshold)


def auto_close_shift_and_flag(shift, reason: str = "inactivity/power_outage"):
    """Auto-close shift and raise anomaly flag if needed."""
    return anomaly_service.auto_close_shift_and_flag(shift, reason=reason)


def auto_close_daysheet_if_needed(daysheet, reason: str = "closing_time_passed"):
    """Auto-close the daysheet (delegates to AnomalyService)."""
    return anomaly_service.auto_close_daysheet_if_needed(daysheet, reason=reason)


# helpers re-exported
def user_is_attendant(user) -> bool:
    """Compatibility wrapper for checking if a user is an attendant."""
    return user_is_attendant_static(user)


def _infer_payment_type_from_job(job):
    """Internal helper to infer payment type from a job (delegates to AnomalyService static helper)."""
    return anomaly_service._infer_payment_type_from_job_static(job)


def get_user_branches(user):
    """
    Return list of branch dicts for the user by delegating to BranchService.
    Each dict is like: {'id': <pk>, 'name': <display name>, 'city': <branch_city>, 'is_manager': True/False}
    """
    return branch_service.get_user_branches(user)


def get_branch_queue_summary(branch_id, limit=20):
    """
    Return branch queue summary by delegating to BranchService.
    Each list item contains lightweight job metadata for UI.
    """
    return branch_service.get_branch_queue_summary(branch_id, limit=limit)
