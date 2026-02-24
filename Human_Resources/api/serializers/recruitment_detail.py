from rest_framework import serializers

from Human_Resources.api.serializers.recruitment_list import (
    RecruitmentListSerializer,
)

from hr_workflows.models import RecruitmentEvaluation


class RecruitmentDetailSerializer(RecruitmentListSerializer):

    evaluation           = serializers.SerializerMethodField()
    screening_evaluation = serializers.SerializerMethodField()
    interview_evaluation = serializers.SerializerMethodField()
    transition_logs      = serializers.SerializerMethodField()

    class Meta(RecruitmentListSerializer.Meta):
        fields = RecruitmentListSerializer.Meta.fields + [
            "evaluation",
            "screening_evaluation",
            "interview_evaluation",
            "transition_logs",
        ]

    def get_transition_logs(self, obj):
        logs = obj.transition_logs.order_by("created_at")
        result = []
        prev_time = obj.created_at

        for log in logs:
            duration_seconds = int((log.created_at - prev_time).total_seconds())
            result.append({
                "action":           log.action,
                "new_stage":        log.new_stage,
                "previous_stage":   log.previous_stage,
                "performed_by":     f"{log.performed_by.first_name} {log.performed_by.last_name}" if log.performed_by else "—",
                "created_at":       log.created_at,
                "duration_seconds": duration_seconds,
            })
            prev_time = log.created_at

        return result

    def get_evaluation(self, obj):
        evaluation = RecruitmentEvaluation.objects.filter(
            application=obj,
            stage=obj.current_stage
        ).first()

        if not evaluation:
            return None

        return self._serialize_evaluation(evaluation)

    def get_screening_evaluation(self, obj):
        evaluation = RecruitmentEvaluation.objects.filter(
            application=obj,
            stage='screening'
        ).first()
        return self._serialize_evaluation(evaluation) if evaluation else None

    def get_interview_evaluation(self, obj):
        evaluation = RecruitmentEvaluation.objects.filter(
            application=obj,
            stage='interview'
        ).first()
        return self._serialize_evaluation(evaluation) if evaluation else None

    def _serialize_evaluation(self, evaluation):
        return {
            "stage":          evaluation.stage,
            "is_finalized":   evaluation.is_finalized,
            "weighted_score": evaluation.weighted_score,
            "created_at":     evaluation.created_at,

            "career_score":      evaluation.career_score,
            "career_notes":      evaluation.career_notes,
            "experience_score":  evaluation.experience_score,
            "experience_notes":  evaluation.experience_notes,
            "stability_score":   evaluation.stability_score,
            "stability_notes":   evaluation.stability_notes,
            "education_score":   evaluation.education_score,
            "education_notes":   evaluation.education_notes,
            "skills_score":      evaluation.skills_score,
            "skills_notes":      evaluation.skills_notes,

            "communication_score":   evaluation.communication_score,
            "communication_notes":   evaluation.communication_notes,
            "attitude_score":        evaluation.attitude_score,
            "attitude_notes":        evaluation.attitude_notes,
            "role_knowledge_score":  evaluation.role_knowledge_score,
            "role_knowledge_notes":  evaluation.role_knowledge_notes,
            "problem_solving_score": evaluation.problem_solving_score,
            "problem_solving_notes": evaluation.problem_solving_notes,
            "cultural_fit_score":    evaluation.cultural_fit_score,
            "cultural_fit_notes":    evaluation.cultural_fit_notes,
        }