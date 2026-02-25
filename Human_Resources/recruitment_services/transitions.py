# Human_Resources/recruitment_services/transitions.py

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from hr_workflows.models import RecruitmentTransitionLog

from hr_workflows.models import (
    RecruitmentApplication,
    RecruitmentEvaluation,
    RecruitmentPolicy,
)
from hr_workflows.models.recruitment_application import RecruitmentDecision
from Human_Resources.recruitment_services.exceptions import InvalidTransition
from Human_Resources.models.audit import AuditLog


class RecruitmentEngine:
    """
    Absolute orchestration layer for recruitment lifecycle.

    The UI/API layer must NEVER mutate stage or status directly.
    Only actions are allowed.
    """

    # =====================================================
    # PUBLIC ACTION ENTRYPOINT
    # =====================================================

    @classmethod
    @transaction.atomic
    def perform_action(cls, application: RecruitmentApplication, action: str, actor, payload=None):

        cls._ensure_not_terminal(application)

        payload = payload or {}
        previous_stage  = application.current_stage
        previous_status = application.status

        router = {
            "start_screening":     cls._start_screening,
            "schedule_interview":  cls._schedule_interview,
            "complete_interview":  cls._complete_interview,
            "submit_final_review": cls._submit_final_review,
            "approve":             cls._approve,
            "reject":              cls._reject,
            "accept_offer":        cls._accept_offer,
            "decline_offer":       cls._decline_offer,
            "withdraw_offer":      cls._withdraw_offer,
        }

        if action not in router:
            raise InvalidTransition(f"Unknown action '{action}'.")

        application = router[action](application, actor, payload)

        application.stage_updated_at = timezone.now()
        application.save()

        RecruitmentTransitionLog.objects.create(
            application=application,
            action=action,
            performed_by=actor,
            previous_stage=previous_stage,
            new_stage=application.current_stage,
            previous_status=previous_status,
            new_status=application.status,
            payload_snapshot=payload if payload else None,
        )

        # Write immutable audit trail
        AuditLog.objects.create(
            user=actor,
            action=action,
            content_type=ContentType.objects.get_for_model(application),
            object_id=application.pk,
            details=str(payload) if payload else "",
        )

        return application

        # =====================================================
        # WORKFLOW ACTIONS
        # =====================================================

    @staticmethod
    def _start_screening(application, actor, payload):
        if application.current_stage != "submitted":
            raise InvalidTransition("Screening can only start from submitted.")

        application.current_stage = "screening"
        application.assigned_reviewer = actor
        return application

    @staticmethod
    def _schedule_interview(application, actor, payload):
        if application.current_stage != "screening":
            raise InvalidTransition("Interview scheduling allowed only from screening.")

        policy = RecruitmentEngine._get_active_policy()
        evaluation = RecruitmentEngine._get_finalized_evaluation(application, "screening")

        if evaluation.weighted_score < policy.screening_threshold:
            raise InvalidTransition(
                f"Screening threshold not met ({policy.screening_threshold})."
            )

        interview_date = payload.get("interview_date")
        if not interview_date:
            raise InvalidTransition("Interview date is required.")

        application.interview_date = interview_date
        application.current_stage = "interview"

        return application

    @staticmethod
    def _complete_interview(application, actor, payload):
        if application.current_stage != "interview":
            raise InvalidTransition("Interview completion only allowed from interview stage.")

        policy = RecruitmentEngine._get_active_policy()

        if policy.require_interview_date and not application.interview_date:
            raise InvalidTransition("Interview must be scheduled before completion.")

        evaluation = RecruitmentEngine._get_finalized_evaluation(application, "interview")

        if evaluation.weighted_score < policy.interview_threshold:
            raise InvalidTransition(
                f"Interview threshold not met ({policy.interview_threshold})."
            )

        application.current_stage = "final_review"
        return application

    @staticmethod
    def _submit_final_review(application, actor, payload):
        if application.current_stage != "final_review":
            raise InvalidTransition("Final review only allowed from final_review stage.")

        policy = RecruitmentEngine._get_active_policy()

        # Auto-create and finalize the final_review evaluation if it doesn't exist.
        # Final Review is a read-and-confirm stage — no separate scoring panel.
        # The weighted score is derived from the average of screening and interview.
        evaluation = RecruitmentEvaluation.objects.filter(
            application=application,
            stage="final_review",
            is_finalized=True,
        ).first()

        if not evaluation:
            screening_eval = RecruitmentEvaluation.objects.filter(
                application=application,
                stage="screening",
                is_finalized=True,
            ).order_by("-finalized_at").first()

            interview_eval = RecruitmentEvaluation.objects.filter(
                application=application,
                stage="interview",
                is_finalized=True,
            ).order_by("-finalized_at").first()

            if not screening_eval or not interview_eval:
                raise InvalidTransition(
                    "Finalized screening and interview evaluations are required "
                    "before submitting the final review."
                )

            # Composite score: average of both weighted scores
            composite_score = round(
                (screening_eval.weighted_score + interview_eval.weighted_score) / 2, 2
            )

            # Check for an existing unfinalized record to avoid unique constraint clash
            evaluation, _ = RecruitmentEvaluation.objects.get_or_create(
                application=application,
                stage="final_review",
                reviewer=actor,
                defaults={
                    "weighted_score": composite_score,
                    "is_finalized":   True,
                    "finalized_at":   timezone.now(),
                    "finalized_by":   actor,
                }
            )

            # If it already existed but wasn't finalized, finalize it now
            if not evaluation.is_finalized:
                evaluation.weighted_score = composite_score
                evaluation.is_finalized   = True
                evaluation.finalized_at   = timezone.now()
                evaluation.finalized_by   = actor
                evaluation.save()

        if evaluation.weighted_score < policy.final_review_threshold:
            raise InvalidTransition(
                f"Final review threshold not met ({policy.final_review_threshold})."
            )

        application.current_stage = "decision"
        return application

    # =====================================================
    # DECISION PHASE
    # =====================================================

    @staticmethod
    def _approve(application, actor, payload):
        """
        Extend offer. NOT terminal.
        """
        if application.current_stage != "decision":
            raise InvalidTransition("Approval only allowed from decision stage.")

        if application.status != RecruitmentDecision.ACTIVE:
            raise InvalidTransition("Offer can only be extended from active decision state.")

        application.status = RecruitmentDecision.OFFER_EXTENDED
        return application

    @staticmethod
    def _reject(application, actor, payload):
        """
        Reject before offer is extended.
        """
        if application.current_stage != "decision":
            raise InvalidTransition("Rejection only allowed from decision stage.")

        if application.status != RecruitmentDecision.ACTIVE:
            raise InvalidTransition("Cannot reject after offer has been extended.")

        application.status = RecruitmentDecision.REJECTED
        application.closed_at = timezone.now()
        return application
    
    @staticmethod
    def _accept_offer(application, actor, payload):
        """
        Candidate accepts offer → hire approved (terminal).
        Automatically initiates onboarding.
        """
        if application.current_stage != "decision":
            raise InvalidTransition("Offer acceptance only allowed from decision stage.")

        if application.status != RecruitmentDecision.OFFER_EXTENDED:
            raise InvalidTransition("No active offer to accept.")

        application.status = RecruitmentDecision.HIRE_APPROVED
        application.closed_at = timezone.now()

        # Copy branch from job offer → application
        try:
            if application.job_offer and application.job_offer.branch:
                application.recommended_branch = application.job_offer.branch
        except application.__class__.job_offer.RelatedObjectDoesNotExist:
            pass

        # Trigger onboarding automatically
        from hr_workflows.onboarding_engine import OnboardingEngine
        OnboardingEngine.initiate(application=application, initiated_by=actor)

        return application

    @staticmethod
    def _decline_offer(application, actor, payload):
        """
        Candidate declines offer → rejected (terminal).
        """
        if application.current_stage != "decision":
            raise InvalidTransition("Offer decline only allowed from decision stage.")

        if application.status != RecruitmentDecision.OFFER_EXTENDED:
            raise InvalidTransition("No active offer to decline.")

        application.status = RecruitmentDecision.REJECTED
        application.closed_at = timezone.now()
        return application

    @staticmethod
    def _withdraw_offer(application, actor, payload):
        """
        Company rescinds offer → withdrawn (terminal).
        """
        if application.current_stage != "decision":
            raise InvalidTransition("Offer withdrawal only allowed from decision stage.")

        if application.status != RecruitmentDecision.OFFER_EXTENDED:
            raise InvalidTransition("No active offer to withdraw.")

        application.status = RecruitmentDecision.WITHDRAWN
        application.closed_at = timezone.now()
        return application

    # =====================================================
    # INTERNAL GUARDS
    # =====================================================

    @staticmethod
    def _get_active_policy():
        policy = RecruitmentPolicy.objects.filter(is_active=True).first()
        if not policy:
            raise ValidationError("No active recruitment policy configured.")
        return policy

    @staticmethod
    def _get_finalized_evaluation(application, stage):
        evaluation = (
            RecruitmentEvaluation.objects
            .filter(
                application=application,
                stage=stage,
                is_finalized=True,
            )
            .order_by("-finalized_at")
            .first()
        )

        if not evaluation:
            raise InvalidTransition(
                f"Finalized evaluation required for stage '{stage}'."
            )

        return evaluation

    @staticmethod
    def _ensure_not_terminal(application):
        if application.is_terminal:
            raise InvalidTransition("Cannot modify a closed application.")