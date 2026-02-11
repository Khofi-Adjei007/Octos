# Human_Resources/api/serializers/recruitment.py

from rest_framework import serializers
from django.core.validators import RegexValidator

PHONE_REGEX = RegexValidator(
    regex=r'^\+?\d{7,15}$',
    message="Phone must be in the format +233XXXXXXXXX or XXXXXXXXX."
)


class RecommendCandidateSerializer(serializers.Serializer):
    """
    Input serializer for recommending a candidate.
    Used by branch managers or authorized personnel.
    """

    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)

    phone = serializers.CharField(
        max_length=15,
        validators=[PHONE_REGEX],
    )

    email = serializers.EmailField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    role_applied_for = serializers.CharField(max_length=255)

    resume = serializers.FileField(
        required=False,
        allow_null=True,
    )

    cover_letter = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    def validate(self, attrs):
        """
        Cross-field validation.
        """

        email = attrs.get("email")
        if email == "":
            attrs["email"] = None

        return attrs
