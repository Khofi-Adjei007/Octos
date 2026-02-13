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
            "score": evaluation.score,
            "notes": evaluation.notes,
            "created_at": evaluation.created_at,
        }
