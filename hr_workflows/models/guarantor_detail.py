# hr_workflows/models/guarantor_detail.py

from django.db import models


class GuarantorDetail(models.Model):
    """
    Cashier-specific guarantor information.
    Required when employee role handles cash.
    Linked to the onboarding record.
    """

    onboarding = models.OneToOneField(
        "hr_workflows.OnboardingRecord",
        on_delete=models.CASCADE,
        related_name="guarantor",
    )

    full_name = models.CharField(max_length=255)
    ghana_card_number = models.CharField(max_length=50)
    ghana_card_upload = models.FileField(
        upload_to="onboarding/guarantors/ghana_cards/",
    )
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("verified", "Verified"),
            ("failed", "Failed"),
        ],
        default="pending",
    )
    house_address = models.TextField()
    nearest_landmark = models.CharField(max_length=255)
    guarantee_document = models.FileField(
        upload_to="onboarding/guarantors/documents/",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Guarantor: {self.full_name} for {self.onboarding}"