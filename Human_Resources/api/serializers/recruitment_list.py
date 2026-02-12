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

    # Status normalized
    status = serializers.SerializerMethodField()

    #resume
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
            "created_at",
            "resume_url",
        ]

    def get_status(self, obj):
        return obj.status.lower()

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
