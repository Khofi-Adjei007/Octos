from rest_framework import serializers

from Human_Resources.api.serializers.recruitment_list import (
    RecruitmentListSerializer,
)

from hr_workflows.models import RecruitmentEvaluation


class RecruitmentDetailSerializer(RecruitmentListSerializer):

    evaluation        = serializers.SerializerMethodField()
    screening_evaluation = serializers.SerializerMethodField()
    interview_evaluation = serializers.SerializerMethodField()

    class Meta(RecruitmentListSerializer.Meta):
        fields = RecruitmentListSerializer.Meta.fields + [
            "evaluation",
            "screening_evaluation",
            "interview_evaluation",
        ]

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
            # Meta
            "stage":          evaluation.stage,
            "is_finalized":   evaluation.is_finalized,
            "weighted_score": evaluation.weighted_score,
            "created_at":     evaluation.created_at,

            # Screening criteria
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

            # Interview criteria
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