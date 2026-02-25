# hr_workflows/onboarding_engine.py

from django.db import transaction
from django.utils import timezone

from hr_workflows.models.onboarding_record import OnboardingRecord, OnboardingStatus
from hr_workflows.models.onboarding_phase import OnboardingPhase, PhaseStatus
from hr_workflows.models.guarantor_detail import GuarantorDetail
# Create or update Employee record from onboarding data
from employees.models import Employee


class OnboardingError(Exception):
    pass


class OnboardingEngine:
    """
    Absolute orchestration layer for employee onboarding lifecycle.

    The UI/API layer must NEVER mutate onboarding records directly.
    Only actions through this engine are allowed.

    Phase 1 — Setup (HR)
    Phase 2 — Documentation (HR)
    Phase 3 — Reporting Confirmation (Branch Manager)
    """

    # =====================================================
    # INITIATION
    # =====================================================

    @classmethod
    @transaction.atomic
    def initiate(cls, application, initiated_by=None):
        """
        Called automatically when application hits hire_approved.
        Creates the onboarding record and three phase records.
        Safe to call — will not duplicate if record already exists.
        """

        # Guard against duplicates
        if hasattr(application, "onboarding"):
            return application.onboarding

        record = OnboardingRecord.objects.create(
            application=application,
            status=OnboardingStatus.PENDING,
            initiated_by=initiated_by,
        )

        # Create all three phases upfront
        for phase_number in [1, 2, 3]:
            OnboardingPhase.objects.create(
                onboarding=record,
                phase_number=phase_number,
                status=PhaseStatus.PENDING,
            )

        return record

    # =====================================================
    # PHASE 1 — SETUP
    # =====================================================

    @classmethod
    @transaction.atomic
    def complete_phase_one(cls, record, actor, data):
        """
        HR completes personal information and branch assignment.
        Creates the employee system account on completion.
        """
        cls._ensure_correct_phase(record, 1)

        phase = cls._get_phase(record, 1)

        # Apply personal information
        phase.house_number = data.get("house_number", "")
        phase.nearest_landmark = data.get("nearest_landmark", "")
        phase.ghana_card_number = data.get("ghana_card_number", "")
        phase.emergency_contact_name = data.get("emergency_contact_name", "")
        phase.emergency_contact_phone = data.get("emergency_contact_phone", "")
        phase.emergency_contact_relationship = data.get("emergency_contact_relationship", "")
        phase.notes = data.get("notes", "")

        # Validate required fields
        required = [
            "house_number",
            "nearest_landmark",
            "ghana_card_number",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
        ]
        cls._validate_required(data, required)

        # Mark phase complete
        phase.status = PhaseStatus.COMPLETED
        phase.completed_by = actor
        phase.completed_at = timezone.now()
        phase.save()

        # Advance record
        record.current_phase = 2
        record.status = OnboardingStatus.IN_PROGRESS
        if not record.started_at:
            record.started_at = timezone.now()
        record.save()

        return record

    # =====================================================
    # PHASE 2 — DOCUMENTATION
    # =====================================================

    @classmethod
    @transaction.atomic
    def complete_phase_two(cls, record, actor, data, files=None):
        """
        HR completes documentation.
        Guarantor details required if role handles cash.
        """
        cls._ensure_correct_phase(record, 2)

        phase = cls._get_phase(record, 2)
        files = files or {}

        # Validate required fields
        required = [
            "contract_signed",
            "bank_name",
            "bank_account_number",
            "ssnit_number",
            "tin_number",
        ]
        cls._validate_required(data, required)

        # ── Coerce contract_signed to a real bool ──────────────────────────
        # FormData always sends strings. Django BooleanField rejects "true"/"false".
        raw_signed = data.get("contract_signed")
        if isinstance(raw_signed, str):
            contract_signed = raw_signed.lower() in ("true", "1", "yes")
        else:
            contract_signed = bool(raw_signed)

        if not contract_signed:
            raise OnboardingError("Contract must be signed before proceeding.")

        # Apply documentation fields
        phase.contract_signed = contract_signed
        phase.contract_signed_date = data.get("contract_signed_date") or None
        phase.ghana_card_verification_status = data.get(
            "ghana_card_verification_status", "pending"
        )
        phase.bank_name = data.get("bank_name", "")
        phase.bank_account_number = data.get("bank_account_number", "")
        phase.ssnit_number = data.get("ssnit_number", "")
        phase.tin_number = data.get("tin_number", "")
        phase.notes = data.get("notes", "")

        if "contract_upload" in files:
            phase.contract_upload = files["contract_upload"]

        if "ghana_card_upload" in files:
            phase.ghana_card_upload = files["ghana_card_upload"]

        # Guarantor check for cash-handling roles
        if cls._requires_guarantor(record):
            cls._save_guarantor(record, data, files)

        # Mark phase complete
        phase.status = PhaseStatus.COMPLETED
        phase.completed_by = actor
        phase.completed_at = timezone.now()
        phase.save()

        # Advance record
        record.current_phase = 3
        record.save()

        return record

    # =====================================================
    # PHASE 3 — REPORTING CONFIRMATION
    # =====================================================

    @classmethod
    @transaction.atomic
    def complete_phase_three(cls, record, actor):
        """
        Branch manager confirms employee has physically reported.
        Marks employee fully active on completion.
        """
        cls._ensure_correct_phase(record, 3)

        phase = cls._get_phase(record, 3)

        phase.reported_confirmed = True
        phase.confirmed_at = timezone.now()
        phase.confirmed_by = actor
        phase.status = PhaseStatus.COMPLETED
        phase.completed_by = actor
        phase.completed_at = timezone.now()
        phase.save()

        # Mark onboarding complete
        record.status = OnboardingStatus.COMPLETED
        record.completed_at = timezone.now()
        record.save()

        # Activate employee account
    @classmethod
    @transaction.atomic
    def complete_phase_three(cls, record, actor):
        """
        Branch manager confirms employee has physically reported.
        Marks employee fully active on completion.
        """
        cls._ensure_correct_phase(record, 3)

        phase = cls._get_phase(record, 3)

        phase.reported_confirmed = True
        phase.confirmed_at = timezone.now()
        phase.confirmed_by = actor
        phase.status = PhaseStatus.COMPLETED
        phase.completed_by = actor
        phase.completed_at = timezone.now()
        phase.save()

        # Mark onboarding complete
        record.status = OnboardingStatus.COMPLETED
        record.completed_at = timezone.now()
        record.save()


        phase1 = cls._get_phase(record, 1)
        phase2 = cls._get_phase(record, 2)
        application = record.application
        applicant = application.applicant

        try:
            job_offer = application.job_offer
        except Exception:
            job_offer = None

        employee, created = Employee.objects.get_or_create(
            personal_email=applicant.email,
            defaults={
                "first_name":          applicant.first_name,
                "last_name":           applicant.last_name,
                "phone_number":        applicant.phone,
                "national_id_number":  applicant.national_id or "",
                "gender":              applicant.gender or "",
                "position_title":      application.role_applied_for,
                "branch":              application.recommended_branch,
                "hire_date":           job_offer.start_date if job_offer else None,
                "current_salary":      job_offer.salary if job_offer else None,
                "bank_name":           phase2.bank_name,
                "bank_account_number": phase2.bank_account_number,
                "ssnit_number":        phase2.ssnit_number,
                "tin_number":          phase2.tin_number,
                "employment_status":   "ACTIVE",
                "is_active":           True,
            }
        )

        if not created:
            employee.employment_status = "ACTIVE"
            employee.is_active = True
            employee.branch = application.recommended_branch
            employee.save(update_fields=["employment_status", "is_active", "branch"])

        # Link employee back to onboarding record
        record.employee = employee
        record.save(update_fields=["employee"])
        # Mark application as onboarding complete
        application.status = "onboarding_complete"
        application.save(update_fields=["status"])

        return record

    # =====================================================
    # STALL CHECKING
    # =====================================================

    @classmethod
    def check_stalled(cls, record):
        """
        Returns alert level based on days since initiation.
        0 = no alert, 3 = day 3 alert, 5 = day 5 escalation, 7 = stalled
        """
        if record.status == OnboardingStatus.COMPLETED:
            return 0

        days = record.days_since_initiated

        if days >= 7 and not record.alert_sent_day_7:
            return 7
        if days >= 5 and not record.alert_sent_day_5:
            return 5
        if days >= 3 and not record.alert_sent_day_3:
            return 3

        return 0

    # =====================================================
    # INTERNAL HELPERS
    # =====================================================

    @staticmethod
    def _get_phase(record, phase_number):
        try:
            return OnboardingPhase.objects.get(
                onboarding=record,
                phase_number=phase_number,
            )
        except OnboardingPhase.DoesNotExist:
            raise OnboardingError(f"Phase {phase_number} not found for this onboarding record.")

    @staticmethod
    def _ensure_correct_phase(record, expected_phase):
        if record.status == OnboardingStatus.COMPLETED:
            raise OnboardingError("Onboarding is already completed.")
        if record.current_phase != expected_phase:
            raise OnboardingError(
                f"Cannot complete phase {expected_phase}. "
                f"Current phase is {record.current_phase}."
            )

    @staticmethod
    def _validate_required(data, fields):
        missing = [f for f in fields if not data.get(f)]
        if missing:
            raise OnboardingError(
                f"Missing required fields: {', '.join(missing)}"
            )

    @staticmethod
    def _requires_guarantor(record):
        """
        Returns True if the employee's role handles cash.
        Currently checks for cashier role code.
        Extend this list as needed.
        """
        application = record.application
        role = getattr(application, "role_applied_for", "").upper()
        return "CASHIER" in role

    @staticmethod
    def _save_guarantor(record, data, files):
        required_guarantor_fields = [
            "guarantor_full_name",
            "guarantor_ghana_card_number",
            "guarantor_house_address",
            "guarantor_nearest_landmark",
        ]

        missing = [f for f in required_guarantor_fields if not data.get(f)]
        if missing:
            raise OnboardingError(
                f"Guarantor details required for this role. Missing: {', '.join(missing)}"
            )

        if "guarantor_ghana_card_upload" not in files:
            raise OnboardingError("Guarantor Ghana Card upload is required.")

        if "guarantor_guarantee_document" not in files:
            raise OnboardingError("Guarantor signed guarantee document is required.")

        GuarantorDetail.objects.update_or_create(
            onboarding=record,
            defaults={
                "full_name": data["guarantor_full_name"],
                "ghana_card_number": data["guarantor_ghana_card_number"],
                "ghana_card_upload": files["guarantor_ghana_card_upload"],
                "verification_status": data.get("guarantor_verification_status", "pending"),
                "house_address": data["guarantor_house_address"],
                "nearest_landmark": data["guarantor_nearest_landmark"],
                "guarantee_document": files["guarantor_guarantee_document"],
            },
        )