from rest_framework import serializers
from hr_workflows.models import RecruitmentApplication


class RecruitmentListSerializer(serializers.ModelSerializer):

    # Applicant info
    first_name = serializers.CharField(source="applicant.first_name")
    last_name = serializers.CharField(source="applicant.last_name")
    email = serializers.CharField(source="applicant.email", allow_null=True)

    # Role
    role_applied_for = serializers.CharField()

    # Branch name
    branch_name = serializers.SerializerMethodField()

    # Recommendation info
    recommender_name = serializers.SerializerMethodField()
    recommender_branch = serializers.SerializerMethodField()

    # Status normalized (terminal)
    status = serializers.SerializerMethodField()

    # NEW: workflow stage
    current_stage = serializers.SerializerMethodField()

    # NEW: reviewer
    assigned_reviewer = serializers.SerializerMethodField()

    # NEW: interview schedule
    interview_date = serializers.DateTimeField(allow_null=True)

    # NEW: priority
    priority = serializers.CharField()

    # NEW: stage timestamp
    stage_updated_at = serializers.DateTimeField()

    # NEW: freshness
    is_new = serializers.SerializerMethodField()

    # Resume
    resume_url = serializers.SerializerMethodField()

    class Meta:
        model = RecruitmentApplication
        fields = [
            "id",
            "first_name",
            "last_name",
            "role_applied_for",
            "email",
            "branch_name",
            "source",
            "recommender_name",
            "recommender_branch",
            "status",
            "current_stage",
            "assigned_reviewer",
            "interview_date",
            "priority",
            "stage_updated_at",
            "is_new",
            "created_at",
            "resume_url",
        ]

    def get_status(self, obj):
        return obj.status.lower()

    def get_current_stage(self, obj):
        return obj.current_stage.lower()

    def get_assigned_reviewer(self, obj):
        if obj.assigned_reviewer:
            return f"{obj.assigned_reviewer.first_name} {obj.assigned_reviewer.last_name}"
        return None

    def get_is_new(self, obj):
        return obj.is_new

    def get_branch_name(self, obj):
        if obj.recommended_branch:
            return obj.recommended_branch.name
        return None

    def get_recommender_name(self, obj):
        if obj.recommended_by:
            return f"{obj.recommended_by.first_name} {obj.recommended_by.last_name}"
        return None

    def get_recommender_branch(self, obj):
        if obj.recommended_by and obj.recommended_by.branch:
            return obj.recommended_by.branch.name
        return None

    def get_resume_url(self, obj):
        if obj.resume:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.resume.url)
            return obj.resume.url
        return None
