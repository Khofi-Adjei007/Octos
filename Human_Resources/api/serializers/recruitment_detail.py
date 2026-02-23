from rest_framework import serializers

from Human_Resources.api.serializers.recruitment_list import (
    RecruitmentListSerializer,
)

from hr_workflows.models import RecruitmentEvaluation


class RecruitmentDetailSerializer(RecruitmentListSerializer):

    evaluation = serializers.SerializerMethodField()

    class Meta(RecruitmentListSerializer.Meta):
        fields = RecruitmentListSerializer.Meta.fields + [
            "evaluation",
        ]

    def get_evaluation(self, obj):
        evaluation = RecruitmentEvaluation.objects.filter(
            application=obj,
            stage=obj.current_stage
        ).first()

        if not evaluation:
            return None

        return {
            "stage": evaluation.stage,
            "career_score": evaluation.career_score,
            "career_notes": evaluation.career_notes,
            "experience_score": evaluation.experience_score,
            "experience_notes": evaluation.experience_notes,
            "stability_score": evaluation.stability_score,
            "stability_notes": evaluation.stability_notes,
            "education_score": evaluation.education_score,
            "education_notes": evaluation.education_notes,
            "skills_score": evaluation.skills_score,
            "skills_notes": evaluation.skills_notes,
            "weighted_score": evaluation.weighted_score,
            "is_finalized": evaluation.is_finalized,
            "created_at": evaluation.created_at,
        }
