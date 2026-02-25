from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import get_object_or_404

from hr_workflows.models import RecruitmentApplication, JobOffer
from Human_Resources.services.query_scope import scoped_recruitment_queryset
from Human_Resources.recruitment_services.transitions import RecruitmentEngine
from Human_Resources.recruitment_services.exceptions import InvalidTransition
from Human_Resources.recruitment_services.permissions import RecruitmentPermissions
from Human_Resources.api.views.recruitment_transition import user_has_recruitment_permission
from Human_Resources.api.serializers.recruitment_detail import RecruitmentDetailSerializer


class ExtendOfferAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):

        queryset    = scoped_recruitment_queryset(request.user)
        application = get_object_or_404(queryset, pk=pk)

        # Permission check
        if not user_has_recruitment_permission(request.user, RecruitmentPermissions.HIRE):
            return Response(
                {"detail": "You do not have permission to extend offers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate required fields
        required = ['salary', 'employment_type', 'start_date']
        for field in required:
            if not request.data.get(field):
                return Response(
                    {"detail": f"'{field}' is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Save offer details
        JobOffer.objects.update_or_create(
            application=application,
            defaults={
                'created_by':        request.user,
                'salary':            request.data.get('salary'),
                'employment_type':   request.data.get('employment_type'),
                'start_date':        request.data.get('start_date'),
                'branch_id':         request.data.get('branch_id') or None,
                'probation_period':  request.data.get('probation_period', '3_months'),
                'offer_expiry_date': request.data.get('offer_expiry_date') or None,
                'notes':             request.data.get('notes', ''),
            }
        )

        # Trigger approve transition — pass a plain dict, not request.data
        try:
            RecruitmentEngine.perform_action(
                application=application,
                action='approve',
                actor=request.user,
                payload={},
            )
        except InvalidTransition as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application.refresh_from_db()
        serializer = RecruitmentDetailSerializer(
            application,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)