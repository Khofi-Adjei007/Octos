# jobs/services.py
"""
Class-based services for jobs, shifts, daysheets, anomalies and shadow logging.

This module is self-contained and intentionally avoids importing from jobs.jobs_services
to prevent circular imports. It uses Django models directly and provides preconfigured
service instances at the bottom for backward compatibility via the facade.
"""
from decimal import Decimal
import hashlib
import hmac
from typing import Optional, Tuple, Dict, Any
from datetime import timedelta
import logging

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.db import models

from .models import (
    Job,
    JobRecord,
    DailySale,
    DaySheet,
    DaySheetShift,
    StatusLog,
    ShadowLogEvent,
    CorrectionEntry,
    AnomalyFlag,
)
from jobs.models import ServiceType, ServicePricingRule
import pytz

logger = logging.getLogger(__name__)

# ---------------------------
# Adapters / Interfaces
# ---------------------------
class PINVerifier:
    """Default PIN verifier. Replace with your real implementation or inject a different instance."""
    def verify(self, user, pin: str) -> bool:
        if not pin:
            return False
        try:
            profile = getattr(user, "profile", None) or getattr(user, "userprofile", None) or getattr(user, "employee", None)
            if profile:
                stored = getattr(profile, "pin", None) or getattr(profile, "pin_code", None)
                if stored and str(stored) == str(pin):
                    return True
        except Exception:
            logger.debug("PINVerifier: error checking profile pin", exc_info=True)
        try:
            stored = getattr(user, "pin", None)
            if stored and str(stored) == str(pin):
                return True
        except Exception:
            logger.debug("PINVerifier: error checking user.pin", exc_info=True)
        try:
            pin_hash = getattr(profile, "pin_hash", None) or getattr(user, "pin_hash", None)
            if pin_hash:
                candidate = hashlib.sha256(str(pin).encode("utf-8")).hexdigest()
                return hmac.compare_digest(candidate, str(pin_hash))
        except Exception:
            logger.debug("PINVerifier: error checking pin_hash", exc_info=True)
        return False


class HQClient:
    """Default HQ client stub (no-op). Replace or subclass to implement real delivery (HTTP/queue)."""
    def deliver(self, payload: dict, signature_secret: Optional[str] = None) -> dict:
        # Simulated response
        now = timezone.now()
        return {"ok": True, "received_at": now.isoformat(), "processed_at": now.isoformat()}


# ---------------------------
# Base Service
# ---------------------------
class BaseService:
    def __init__(self, hq_client: Optional[HQClient] = None, pin_verifier: Optional[PINVerifier] = None):
        self.hq = hq_client or HQClient()
        self.pin_verifier = pin_verifier or PINVerifier()

    # StatusLog helper
    def _create_status_log(self, entity_type: str, entity_id: str, event: str, actor: Optional[dict] = None, payload: Optional[dict] = None) -> StatusLog:
        return StatusLog.objects.create(
            entity_type=entity_type,
            entity_id=str(entity_id),
            event=event,
            actor_id=(actor or {}).get("user_id") if actor else None,
            actor_role=(actor or {}).get("role") if actor else None,
            payload=payload or {},
        )

    # Shadow event helper
    def _create_shadow_event(self, event_type: str, branch_id: Optional[str], actor: Optional[dict], payload: dict, signature_secret: Optional[str] = None) -> ShadowLogEvent:
        ev = ShadowLogEvent.objects.create(
            event_type=event_type,
            branch_id=str(branch_id) if branch_id else None,
            source=payload.get("source", {}),
            actor=actor or {},
            timestamp=payload.get("timestamp", timezone.now()),
            payload=payload,
            signature="",
        )
        # deliver (best-effort)
        try:
            res = self.hq.deliver(payload, signature_secret=signature_secret)
            if res.get("ok"):
                ev.sent_at = timezone.now()
                ev.received_at = res.get("received_at") or timezone.now()
                ev.processed_at = res.get("processed_at") or timezone.now()
                ev.save(update_fields=["sent_at", "received_at", "processed_at"])
        except Exception as exc:
            # Fail silently for core operation but log for diagnostics
            logger.exception("HQ delivery failed for shadow event %s: %s", event_type, exc)
        return ev


# ---------------------------
# Utility helpers (local)
# ---------------------------
def _local_date_for_branch(now, branch):
    tzname = getattr(branch, "timezone", None) or "UTC"
    try:
        local = now.astimezone(pytz.timezone(tzname))
    except Exception:
        local = now
    return local.date()


def _branch_snapshot(branch):
    manager = getattr(branch, "manager", None)
    manager_name = ""
    manager_email = ""
    try:
        if manager:
            get_full = getattr(manager, "get_full_name", None)
            if callable(get_full):
                manager_name = get_full()
            else:
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


# ---------------------------
# Primary services
# ---------------------------
class JobService(BaseService):

    # -------------------------------------------------
    # PRINT SERVICE ENFORCEMENT
    # -------------------------------------------------
    def _is_print_service(self, service: ServiceType) -> bool:
        return service.code in {"A4_PRINT", "A3_PRINT"}

    def _validate_print_variants(
        self,
        *,
        service: ServiceType,
        paper_size: str,
        print_mode: str,
        color_mode: str,
        side_mode: str,
    ):
        if not self._is_print_service(service):
            return

        missing = []
        if not paper_size:
            missing.append("paper_size")
        if not print_mode:
            missing.append("print_mode")
        if not color_mode:
            missing.append("color_mode")
        if not side_mode:
            missing.append("side_mode")

        if missing:
            raise ValueError(
                f"Missing required print options for {service.code}: {', '.join(missing)}"
            )

    # -------------------------------------------------
    # EXISTING LOGIC (UNCHANGED)
    # -------------------------------------------------
    def attach_job_to_daysheet_idempotent(self, job: Job, user=None, daysheet: DaySheet = None, now=None) -> Tuple[DaySheet, bool, bool]:
        if job is None:
            raise ValueError("job is required")
        now = now or timezone.now()

        with transaction.atomic():
            job = Job.objects.select_for_update().get(pk=job.pk)

            if getattr(job, "daysheet_id", None):
                try:
                    existing_ds = DaySheet.objects.get(pk=job.daysheet_id)
                except DaySheet.DoesNotExist:
                    existing_ds = None
                return existing_ds, False, False

            meta = getattr(job, "meta", {}) or {}
            if meta.get("attached_to_daysheet"):
                existing_ds = None
                try:
                    existing_ds = DaySheet.objects.filter(meta__contains={"job_ref": job.pk}).first()
                except Exception:
                    existing_ds = None
                return existing_ds, False, False

            if daysheet is None:
                daysheet, created = DaySheetService(self.hq, self.pin_verifier).get_or_create_daysheet_for_branch(
                    job.branch, user=user, now=now
                )
            else:
                daysheet = DaySheet.objects.select_for_update().get(pk=daysheet.pk)
                created = False

            try:
                unit_price = Decimal(getattr(job, "unit_price", None) or getattr(job, "price", None) or 0)
            except Exception:
                unit_price = Decimal("0.00")

            try:
                deposit = Decimal(getattr(job, "deposit_amount", 0) or 0)
            except Exception:
                deposit = Decimal("0.00")

            qty = int(getattr(job, "quantity", 1) or 1)
            total_for_job = (unit_price * qty) - deposit
            if total_for_job < 0:
                total_for_job = Decimal("0.00")

            payment_type = AnomalyService._infer_payment_type_from_job_static(job)

            DaySheet.objects.filter(pk=daysheet.pk).update(
                total_jobs=F("total_jobs") + 1,
                total_amount=F("total_amount") + total_for_job,
            )

            job.daysheet = daysheet
            meta["attached_to_daysheet"] = True
            job.meta = meta
            job.save()

            actor = {"user_id": getattr(user, "pk", None), "role": getattr(user, "role", None) if user else None}
            payload = {
                "daily_sheet_date": str(daysheet.date),
                "daily_sheet_id": str(daysheet.pk),
                "job_id": str(job.pk),
                "service": getattr(job.service, "name", None),
                "total_amount": float(total_for_job),
                "payment_type": payment_type,
                "timestamp": now.isoformat(),
            }
            self._create_status_log("DaySheet", str(daysheet.pk), "JOB_ATTACHED", actor=actor, payload=payload)
            self._create_shadow_event("JOB_ATTACHED", getattr(job.branch, "pk", None), actor=actor, payload=payload)

            return daysheet, created, True

    def create_instant_job(
        self,
        *,
        branch_id,
        service_id,
        quantity,
        created_by=None,
        customer_name=None,
        customer_phone=None,
        deposit=0,
        description="",
        paper_size=None,
        print_mode=None,
        color_mode=None,
        side_mode=None,
    ):
        svc = ServiceType.objects.get(pk=service_id)

        # ✅ ENFORCE PRINT VARIANTS HERE
        self._validate_print_variants(
            service=svc,
            paper_size=paper_size,
            print_mode=print_mode,
            color_mode=color_mode,
            side_mode=side_mode,
        )

        unit_price = self.resolve_unit_price_safe(
            service=svc,
            paper_size=paper_size,
            print_mode=print_mode,
            color_mode=color_mode,
            side_mode=side_mode,
        )

        qty = int(quantity or 1)
        deposit = Decimal(deposit or 0)
        total = (unit_price * qty) - deposit
        if total < 0:
            total = Decimal("0.00")

        now = timezone.now()

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
                completed_at=now,
                created_by=created_by,
                meta={
                    "paper_size": paper_size,
                    "print_mode": print_mode,
                    "color_mode": color_mode,
                    "side_mode": side_mode,
                },
            )

            JobRecord.objects.create(
                job=job,
                performed_by=created_by,
                time_start=now,
                time_end=now,
                quantity_produced=qty,
                notes="Instant job (auto-priced)",
            )

            DaySheetService(self.hq, self.pin_verifier).get_or_create_daysheet_for_branch(
                job.branch, user=created_by, now=now
            )
            self.attach_job_to_daysheet_idempotent(job, user=created_by, now=now)

            actor = {
                "user_id": getattr(created_by, "pk", None),
                "role": getattr(created_by, "role", None) if created_by else None,
            }
            payload = {
                "job_id": str(job.pk),
                "branch_id": str(branch_id),
                "service": svc.name,
                "unit_price": float(unit_price),
                "quantity": qty,
                "total_amount": float(job.total_amount),
                "timestamp": now.isoformat(),
            }
            self._create_status_log("Job", str(job.pk), "JOB_CREATED_INSTANT", actor=actor, payload=payload)
            self._create_shadow_event("JOB_CREATED_INSTANT", branch_id, actor=actor, payload=payload)

        return job

    # -------------------------------------------------
    # PRICING (UNCHANGED)
    # -------------------------------------------------
    def resolve_unit_price(
        self,
        *,
        service: ServiceType,
        paper_size: str = None,
        print_mode: str = None,
        color_mode: str = None,
        side_mode: str = None,
    ) -> Decimal:
        try:
            rule = ServicePricingRule.objects.get(
                service_type=service,
                is_active=True,
                paper_size=paper_size,
                print_mode=print_mode,
                color_mode=color_mode,
                side_mode=side_mode,
            )
            return rule.unit_price
        except ServicePricingRule.DoesNotExist:
            raise ValueError(
                f"No pricing rule found for {service.code} "
                f"[{paper_size}, {print_mode}, {color_mode}, {side_mode}]"
            )

    def resolve_unit_price_safe(
        self,
        *,
        service: ServiceType,
        paper_size: str = None,
        print_mode: str = None,
        color_mode: str = None,
        side_mode: str = None,
    ) -> Decimal:
        try:
            return self.resolve_unit_price(
                service=service,
                paper_size=paper_size,
                print_mode=print_mode,
                color_mode=color_mode,
                side_mode=side_mode,
            )
        except Exception:
            pass

        rule = ServicePricingRule.objects.filter(
            service_type=service,
            pricing_type="flat",
            is_active=True,
        ).first()

        if rule:
            return rule.unit_price

        return Decimal(getattr(service, "price", "0.00") or "0.00")



class DaySheetService(BaseService):
    def get_or_create_daysheet_for_branch(self, branch, user=None, now=None, allow_reopen=False, shift_name=None) -> Tuple[DaySheet, bool]:
        now = now or timezone.now()
        date_local = _local_date_for_branch(now, branch)
        weekday = date_local.strftime("%A")

        with transaction.atomic():
            sheet = (
                DaySheet.objects.select_for_update()
                .filter(branch=branch, date=date_local, status=DaySheet.STATUS_OPEN)
                .first()
            )
            if sheet:
                return sheet, False

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
                meta={},
            )
            try:
                self._create_status_log("DaySheet", str(sheet.pk), "DAY_SHEET_CREATED", actor={"user_id": getattr(user, "pk", None), "role": getattr(user, "role", None) if user else None}, payload={"date": str(sheet.date)})
                self._create_shadow_event("DAY_SHEET_CREATED", getattr(branch, "pk", None), actor={"user_id": getattr(user, "pk", None)}, payload={"date": str(sheet.date)})
            except Exception as exc:
                logger.exception("DaySheetService: failed to create status or shadow log for daysheet %s: %s", getattr(sheet, "pk", None), exc)
            return sheet, True


class ShiftService(BaseService):
    def start_shift(self, branch, user, now=None, role: str = "ATTENDANT", shift_name: Optional[str] = None) -> DaySheetShift:
        now = now or timezone.now()
        daysheet, created = DaySheetService(self.hq, self.pin_verifier).get_or_create_daysheet_for_branch(branch, user=user, now=now, shift_name=shift_name)
        with transaction.atomic():
            shift = DaySheetShift.objects.select_for_update().filter(daysheet=daysheet, user=user, status=DaySheetShift.SHIFT_OPEN).first()
            if shift:
                return shift
            shift = DaySheetShift.objects.create(
                daysheet=daysheet,
                user=user,
                role=role,
                shift_start=now,
                status=DaySheetShift.SHIFT_OPEN,
                opening_cash=Decimal("0.00"),
            )
            actor = {"user_id": getattr(user, "pk", None), "role": getattr(user, "role", None) if user else None}
            payload = {"shift_id": str(shift.pk), "daysheet_id": str(daysheet.pk), "timestamp": now.isoformat()}
            try:
                self._create_status_log("DaySheetShift", str(shift.pk), "SHIFT_STARTED", actor=actor, payload=payload)
                self._create_shadow_event("SHIFT_STARTED", getattr(branch, "pk", None), actor=actor, payload=payload)
            except Exception as exc:
                logger.exception("ShiftService.start_shift: failed to create logs for shift %s: %s", getattr(shift, "pk", None), exc)
            return shift

    def close_shift(self, shift: DaySheetShift, user, closing_cash: Decimal, pin: str, now=None) -> DaySheetShift:
        now = now or timezone.now()
        if shift.status not in (DaySheetShift.SHIFT_OPEN,):
            raise ValueError("Shift is not open and cannot be closed.")
        if not self.pin_verifier.verify(user, pin):
            shift.pin_failed_attempts = F("pin_failed_attempts") + 1
            shift.save(update_fields=["pin_failed_attempts"])
            raise PermissionError("Invalid PIN")
        with transaction.atomic():
            shift.shift_end = now
            shift.status = DaySheetShift.SHIFT_CLOSED
            shift.closing_cash = Decimal(closing_cash or 0)
            shift.pin_verified_at = now
            shift.pin_verified_by = user
            shift.submitted = True
            shift.save()
            actor = {"user_id": getattr(user, "pk", None), "role": getattr(user, "role", None) if user else None}
            payload = {
                "shift_id": str(shift.pk),
                "daysheet_id": str(shift.daysheet.pk),
                "closing_cash": float(shift.closing_cash or 0),
                "timestamp": now.isoformat(),
            }
            try:
                self._create_status_log("DaySheetShift", str(shift.pk), "SHIFT_CLOSED", actor=actor, payload=payload)
                self._create_shadow_event("SHIFT_CLOSED", getattr(shift.daysheet.branch, "pk", None), actor=actor, payload=payload)
            except Exception as exc:
                logger.exception("ShiftService.close_shift: failed to create logs for shift %s: %s", getattr(shift, "pk", None), exc)

            # basic mismatch detection
            try:
                jobs_qs = Job.objects.filter(daysheet=shift.daysheet, created_by=shift.user)
                computed_total = jobs_qs.aggregate(total=models.Sum("total_amount"))["total"] or Decimal("0.00")
                tolerance = Decimal("10.00")
                cash_diff = (Decimal(shift.closing_cash or 0) - Decimal(computed_total or 0))
                if abs(cash_diff) > tolerance:
                    try:
                        AnomalyFlag.objects.create(
                            daily_sheet=shift.daysheet,
                            shift=shift,
                            flag_type=AnomalyFlag.TYPE_MISMATCH_CASH,
                            severity=AnomalyFlag.SEV_HIGH,
                            description=f"Shift cash mismatch: reported {shift.closing_cash} vs computed {computed_total}",
                            notified_to=[{"role": "manager"}, {"role": "hq"}],
                        )
                    except Exception as exc:
                        logger.exception("ShiftService.close_shift: failed to create AnomalyFlag for shift %s: %s", getattr(shift, "pk", None), exc)
            except Exception as exc:
                logger.exception("ShiftService.close_shift: mismatch detection failed for shift %s: %s", getattr(shift, "pk", None), exc)

            return shift


class ManagerService(BaseService):
    def manager_close_day(self, daysheet: DaySheet, manager_user, pin: str, now=None) -> DaySheet:
        now = now or timezone.now()
        open_shifts = daysheet.shifts.filter(status=DaySheetShift.SHIFT_OPEN).exists()
        if open_shifts:
            raise ValueError("Not all shifts are closed. Manager cannot close the day.")
        if not self.pin_verifier.verify(manager_user, pin):
            raise PermissionError("Invalid manager PIN")
        with transaction.atomic():
            daysheet.status = DaySheet.STATUS_BRANCH_CLOSED
            daysheet.closed_at = now
            daysheet.closed_by = manager_user
            daysheet.save()
            actor = {"user_id": getattr(manager_user, "pk", None), "role": getattr(manager_user, "role", None) if manager_user else None}
            payload = {
                "daily_sheet_id": str(daysheet.pk),
                "date": str(daysheet.date),
                "timestamp": now.isoformat(),
                "total_jobs": daysheet.total_jobs,
                "total_amount": float(daysheet.total_amount or 0),
            }
            try:
                self._create_status_log("DaySheet", str(daysheet.pk), "MANAGER_CLOSED", actor=actor, payload=payload)
                self._create_shadow_event("MANAGER_CLOSED", getattr(daysheet.branch, "pk", None), actor=actor, payload=payload)
            except Exception as exc:
                logger.exception("ManagerService.manager_close_day: failed to create logs for daysheet %s: %s", getattr(daysheet, "pk", None), exc)
            return daysheet


class CorrectionService(BaseService):
    def create_correction_entry(self, daysheet: DaySheet, created_by, payload: dict, correction_type: str = CorrectionEntry.TYPE_NOTE, created_for_user=None) -> CorrectionEntry:
        with transaction.atomic():
            ce = CorrectionEntry.objects.create(
                daily_sheet=daysheet,
                shift=payload.get("shift_id") and DaySheetShift.objects.filter(pk=payload.get("shift_id")).first(),
                job=payload.get("job_id") and Job.objects.filter(pk=payload.get("job_id")).first(),
                created_by=created_by,
                created_for_user=created_for_user,
                type=correction_type,
                payload=payload,
                status=CorrectionEntry.STATUS_OPEN,
            )
            actor = {"user_id": getattr(created_by, "pk", None), "role": getattr(created_by, "role", None) if created_by else None}
            try:
                self._create_status_log("CorrectionEntry", str(ce.uuid), "CORRECTION_CREATED", actor=actor, payload=payload)
                self._create_shadow_event("CORRECTION_CREATED", getattr(daysheet.branch, "pk", None), actor=actor, payload=payload)
            except Exception as exc:
                logger.exception("CorrectionService.create_correction_entry: failed to log/shadow for correction %s: %s", getattr(ce, "uuid", None), exc)
            return ce


class AnomalyService(BaseService):
    @staticmethod
    def _infer_payment_type_from_job_static(job):
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

    def detect_duplicate_job(self, job: Job, window_seconds: int = 120) -> Optional[AnomalyFlag]:
        try:
            since = timezone.now() - timedelta(seconds=window_seconds)
            dup = Job.objects.filter(
                branch=job.branch,
                service=job.service,
                total_amount=job.total_amount,
                created_at__gte=since
            ).exclude(pk=job.pk).first()
            if dup:
                af = AnomalyFlag.objects.create(
                    daily_sheet=job.daysheet,
                    shift=None,
                    flag_type=AnomalyFlag.TYPE_DUPLICATE_JOBS,
                    severity=AnomalyFlag.SEV_MEDIUM,
                    description=f"Duplicate job detected: job {job.pk} similar to {dup.pk}",
                    notified_to=[{"role": "manager"}],
                )
                try:
                    self._create_status_log("AnomalyFlag", str(af.uuid), "DUPLICATE_JOB_DETECTED", actor={"user_id": getattr(job.created_by, "pk", None)}, payload={"job": job.pk, "duplicate_of": dup.pk})
                    self._create_shadow_event("DUPLICATE_JOB", getattr(job.branch, "pk", None), actor={"user_id": getattr(job.created_by, "pk", None)}, payload={"job": job.pk, "duplicate_of": dup.pk})
                except Exception as exc:
                    logger.exception("AnomalyService.detect_duplicate_job: failed to create logs for anomaly %s: %s", getattr(af, "uuid", None), exc)
                return af
        except Exception as exc:
            logger.exception("AnomalyService.detect_duplicate_job failed for job %s: %s", getattr(job, "pk", None), exc)
        return None

    def detect_high_free_jobs(self, daysheet: DaySheet, free_ratio_threshold: float = 0.2) -> Optional[AnomalyFlag]:
        try:
            total = daysheet.total_jobs or 0
            if total == 0:
                return None
            free_count = Job.objects.filter(daysheet=daysheet, service__is_priced=False).count()
            ratio = free_count / float(total)
            if ratio >= float(free_ratio_threshold):
                af = AnomalyFlag.objects.create(
                    daily_sheet=daysheet,
                    shift=None,
                    flag_type=AnomalyFlag.TYPE_HIGH_FREE_JOBS,
                    severity=AnomalyFlag.SEV_HIGH,
                    description=f"High free-job ratio: {free_count}/{total} ({ratio:.2f})",
                    notified_to=[{"role": "manager"}, {"role": "hq"}],
                )
                try:
                    self._create_status_log("AnomalyFlag", str(af.uuid), "HIGH_FREE_JOBS", actor=None, payload={"free_count": free_count, "total": total, "ratio": ratio})
                    self._create_shadow_event("HIGH_FREE_JOBS", getattr(daysheet.branch, "pk", None), actor=None, payload={"free_count": free_count, "total": total, "ratio": ratio})
                except Exception as exc:
                    logger.exception("AnomalyService.detect_high_free_jobs: failed to create logs for anomaly %s: %s", getattr(af, "uuid", None), exc)
                return af
        except Exception as exc:
            logger.exception("AnomalyService.detect_high_free_jobs failed for daysheet %s: %s", getattr(daysheet, "pk", None), exc)
        return None

    def auto_close_shift_and_flag(self, shift: DaySheetShift, reason: str = "inactivity/power_outage"):
        now = timezone.now()
        with transaction.atomic():
            if shift.status == DaySheetShift.SHIFT_OPEN:
                shift.status = DaySheetShift.SHIFT_AUTO_CLOSED
                shift.shift_end = now
                shift.save(update_fields=["status", "shift_end"])
                try:
                    af = AnomalyFlag.objects.create(
                        daily_sheet=shift.daysheet,
                        shift=shift,
                        flag_type=AnomalyFlag.TYPE_AUTO_CLOSE,
                        severity=AnomalyFlag.SEV_HIGH,
                        description=f"Auto-closed shift due to {reason}",
                        notified_to=[{"role": "manager"}, {"role": "hq"}],
                    )
                except Exception as exc:
                    logger.exception("AnomalyService.auto_close_shift_and_flag: failed to create AnomalyFlag for shift %s: %s", getattr(shift, "pk", None), exc)
                    af = None
                try:
                    self._create_status_log("DaySheetShift", str(shift.pk), "SHIFT_AUTO_CLOSED", actor=None, payload={"reason": reason, "timestamp": now.isoformat()})
                    self._create_shadow_event("SHIFT_AUTO_CLOSED", getattr(shift.daysheet.branch, "pk", None), actor=None, payload={"reason": reason, "timestamp": now.isoformat()})
                except Exception as exc:
                    logger.exception("AnomalyService.auto_close_shift_and_flag: failed to create logs for auto-closed shift %s: %s", getattr(shift, "pk", None), exc)
                return shift, af
        return shift, None

    def auto_close_daysheet_if_needed(self, daysheet: DaySheet, reason: str = "closing_time_passed"):
        now = timezone.now()
        with transaction.atomic():
            if daysheet.status in (DaySheet.STATUS_OPEN, DaySheet.STATUS_PARTIALLY_CLOSED):
                daysheet.status = DaySheet.STATUS_AUTO_CLOSED
                daysheet.closed_at = now
                daysheet.save(update_fields=["status", "closed_at"])
                try:
                    af = AnomalyFlag.objects.create(
                        daily_sheet=daysheet,
                        shift=None,
                        flag_type=AnomalyFlag.TYPE_AUTO_CLOSE,
                        severity=AnomalyFlag.SEV_CRITICAL,
                        description=f"Auto-closed daysheet due to {reason}",
                        notified_to=[{"role": "hq"}],
                    )
                except Exception as exc:
                    logger.exception("AnomalyService.auto_close_daysheet_if_needed: failed to create AnomalyFlag for daysheet %s: %s", getattr(daysheet, "pk", None), exc)
                    af = None
                try:
                    self._create_status_log("DaySheet", str(daysheet.pk), "DAY_AUTO_CLOSED", actor=None, payload={"reason": reason, "timestamp": now.isoformat()})
                    self._create_shadow_event("DAY_AUTO_CLOSED", getattr(daysheet.branch, "pk", None), actor=None, payload={"reason": reason, "timestamp": now.isoformat()})
                except Exception as exc:
                    logger.exception("AnomalyService.auto_close_daysheet_if_needed: failed to create logs for daysheet auto-close %s: %s", getattr(daysheet, "pk", None), exc)
                return daysheet, af
        return daysheet, None


# ---------------------------
# Branch / user helpers
# ---------------------------
from django.db.models import Q

class BranchService(BaseService):
    """
    Helpers to map users -> branches and produce a branch queue summary for dashboards.
    The implementation is defensive to tolerate different project shapes (branch.manager, branch.users,
    branch.employees, etc). The returned branch dicts are:
      {'id': <pk>, 'name': <display name>, 'city': <branch_city>, 'is_manager': True/False}
    The queue summary returns list of lightweight job dicts for display in UI.
    """
    def get_user_branches(self, user) -> list:
        # Try facade-friendly fast queries, fall back to scanning
        Branch = None
        try:
            from django.apps import apps
            Branch = apps.get_model("branches", "Branch")
        except Exception:
            Branch = None

        results = []
        if Branch is None:
            return results

        seen = set()
        # 1) Try queries using common related names (fast if they exist)
        try:
            qs = Branch.objects.none()
            # manager patterns
            try:
                qs = qs.union(Branch.objects.filter(Q(manager__pk=getattr(user, "pk", None)) | Q(manager__user__pk=getattr(user, "pk", None))))
            except Exception:
                logger.debug("BranchService.get_user_branches: manager-based query not available", exc_info=True)
            # employees/staff/users patterns
            try:
                qs = qs.union(Branch.objects.filter(Q(employees__user__pk=getattr(user, "pk", None)) | Q(staff__user__pk=getattr(user, "pk", None)) | Q(users__pk=getattr(user, "pk", None))))
            except Exception:
                logger.debug("BranchService.get_user_branches: employees/staff/users-based query not available", exc_info=True)

            # If qs contains results, use them
            if qs.exists():
                for b in qs.distinct():
                    bid = b.pk
                    if bid in seen:
                        continue
                    seen.add(bid)
                    results.append({
                        "id": bid,
                        "name": getattr(b, "name", str(b)),
                        "city": getattr(b, "branch_city", "") or getattr(getattr(b, "city", None), "name", "") or "",
                        "is_manager": self._is_manager_of_branch(user, b),
                    })
                return results
        except Exception:
            logger.debug("BranchService.get_user_branches: fast query path failed", exc_info=True)
            # fall through to slower scan

        # 2) Fallback: iterate over all branches and detect relations by attribute access (safe)
        try:
            for b in Branch.objects.all():
                bid = b.pk
                if bid in seen:
                    continue
                is_related = False
                try:
                    # common patterns
                    if getattr(b, "manager", None):
                        mgr = getattr(b, "manager", None)
                        if mgr == user or getattr(mgr, "user", None) == user or getattr(mgr, "pk", None) == getattr(user, "pk", None):
                            is_related = True
                    # employee relations
                    try:
                        emps = getattr(b, "employees", None)
                        if emps is not None:
                            if emps.filter(user__pk=getattr(user, "pk", None)).exists():
                                is_related = True
                    except Exception:
                        pass
                    # users many-to-many
                    try:
                        users_q = getattr(b, "users", None)
                        if users_q is not None and users_q.filter(pk=getattr(user, "pk", None)).exists():
                            is_related = True
                    except Exception:
                        pass
                    if is_related:
                        seen.add(bid)
                        results.append({
                            "id": bid,
                            "name": getattr(b, "name", str(b)),
                            "city": getattr(b, "branch_city", "") or getattr(getattr(b, "city", None), "name", "") or "",
                            "is_manager": self._is_manager_of_branch(user, b),
                        })
                except Exception:
                    # skip problematic branch rows
                    logger.debug("BranchService.get_user_branches: skipping branch %s due to inspection error", getattr(b, "pk", None), exc_info=True)
                    continue
        except Exception:
            logger.exception("BranchService.get_user_branches: failed to iterate branches", exc_info=True)

        return results

    def _is_manager_of_branch(self, user, branch_obj) -> bool:
        try:
            mgr = getattr(branch_obj, "manager", None)
            if mgr is None:
                return False
            # manager might be a User, Employee, or have a user relation
            if mgr == user:
                return True
            if getattr(mgr, "user", None) == user:
                return True
            if getattr(mgr, "pk", None) == getattr(user, "pk", None):
                return True
            return False
        except Exception:
            logger.debug("BranchService._is_manager_of_branch failed for branch %s and user %s", getattr(branch_obj, "pk", None), getattr(user, "pk", None), exc_info=True)
            return False

    def get_branch_queue_summary(self, branch_id, limit: int = 20) -> list:
        """
        Return a list of job summary dicts for the given branch.
        Each entry:
          {
            'id': int,
            'customer_name': str,
            'service': str,
            'status': str,
            'eta': ISO timestamp or None,
            'created_at': ISO timestamp,
            'queue_position': int or None,
            'total_amount': float,
            'created_by': username or None,
            'quantity': int
          }
        """
        Job = None
        try:
            from django.apps import apps
            Job = apps.get_model("jobs", "Job")
        except Exception:
            Job = None

        if Job is None:
            return []

        try:
            # prefer queued / in_progress / ready statuses
            statuses = ["queued", "in_progress", "ready"]
            qs = Job.objects.filter(branch_id=branch_id, status__in=statuses).order_by("queue_position", "created_at")[:limit]
            results = []
            for j in qs:
                results.append({
                    "id": j.pk,
                    "customer_name": getattr(j, "customer_name", "") or "",
                    "service": getattr(getattr(j, "service", None), "name", "") if getattr(j, "service", None) else "",
                    "status": getattr(j, "status", "") or "",
                    "eta": getattr(j, "expected_ready_at", None).isoformat() if getattr(j, "expected_ready_at", None) else None,
                    "created_at": getattr(j, "created_at", None).isoformat() if getattr(j, "created_at", None) else None,
                    "queue_position": getattr(j, "queue_position", None),
                    "total_amount": float(getattr(j, "total_amount", 0) or 0),
                    "created_by": getattr(getattr(j, "created_by", None), "username", None) if getattr(j, "created_by", None) else None,
                    "quantity": int(getattr(j, "quantity", 1) or 1),
                })
            return results
        except Exception as exc:
            logger.debug("BranchService.get_branch_queue_summary: primary query failed, trying fallback ordering: %s", exc)
            # try a more permissive ordering if queue_position doesn't exist
            try:
                qs = Job.objects.filter(branch_id=branch_id, status__in=statuses).order_by("created_at")[:limit]
                results = []
                for j in qs:
                    results.append({
                        "id": j.pk,
                        "customer_name": getattr(j, "customer_name", "") or "",
                        "service": getattr(getattr(j, "service", None), "name", "") if getattr(j, "service", None) else "",
                        "status": getattr(j, "status", "") or "",
                        "eta": getattr(j, "expected_ready_at", None).isoformat() if getattr(j, "expected_ready_at", None) else None,
                        "created_at": getattr(j, "created_at", None).isoformat() if getattr(j, "created_at", None) else None,
                        "queue_position": getattr(j, "queue_position", None),
                        "total_amount": float(getattr(j, "total_amount", 0) or 0),
                        "created_by": getattr(getattr(j, "created_by", None), "username", None) if getattr(j, "created_by", None) else None,
                        "quantity": int(getattr(j, "quantity", 1) or 1),
                    })
                return results
            except Exception:
                logger.exception("BranchService.get_branch_queue_summary fallback query failed for branch %s", branch_id)
                return []




# ---------------------------
# Utility: user_is_attendant
# ---------------------------
def user_is_attendant_static(user) -> bool:
    try:
        emp = getattr(user, "employee", None) or getattr(user, "userprofile", None)
        if emp and hasattr(emp, "role") and emp.role:
            return getattr(emp.role, "code", "").upper() == "ATTENDANT"
    except Exception:
        pass
    try:
        role = getattr(user, "role", None)
        if role and getattr(role, "code", "").upper() == "ATTENDANT":
            return True
    except Exception:
        pass
    try:
        if user.groups.filter(name__iexact="attendant").exists():
            return True
    except Exception:
        pass
    return False


# ---------------------------
# Preconfigured singletons (facade targets)
# ---------------------------
_default_hq = HQClient()
_default_pin = PINVerifier()

job_service = JobService(hq_client=_default_hq, pin_verifier=_default_pin)
daysheet_service = DaySheetService(hq_client=_default_hq, pin_verifier=_default_pin)
shift_service = ShiftService(hq_client=_default_hq, pin_verifier=_default_pin)
manager_service = ManagerService(hq_client=_default_hq, pin_verifier=_default_pin)
correction_service = CorrectionService(hq_client=_default_hq, pin_verifier=_default_pin)
anomaly_service = AnomalyService(hq_client=_default_hq, pin_verifier=_default_pin)
branch_service = BranchService(hq_client=_default_hq, pin_verifier=_default_pin)
