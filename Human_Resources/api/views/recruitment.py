from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from hr_workflows.models import applicant as Applicant
from Human_Resources.api.serializers.recruitment import RecommendCandidateSerializer
from Human_Resources.recruitment_services.commands import recommend_applicant
from Human_Resources.recruitment_services.exceptions import RecruitmentError


class RecommendCandidateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RecommendCandidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        applicant, _ = Applicant.objects.get_or_create(
            phone=data["phone"],
            defaults={
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "email": data.get("email"),
            },
        )

        try:
            application = recommend_applicant(
                applicant=applicant,
                role_applied_for=data["role_applied_for"],
                actor=request.user,
            )
        except RecruitmentError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "application_id": application.id,
                "status": application.status,
                "source": application.source,
            },
            status=status.HTTP_201_CREATED,
        )
