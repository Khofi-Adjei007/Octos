# human_resources/constants.py

from django.db import models


class RecruitmentStatus(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    SCREENING = "screening", "Screening"
    INTERVIEW = "interview", "Interview"
    FINAL_REVIEW = "final_review", "Final Review"
    OFFER = "offer", "Offer"
    ONBOARDED = "onboarded", "Onboarded"
    REJECTED = "rejected", "Rejected"


class RecruitmentSource(models.TextChoices):
    PUBLIC = "public", "Public"
    RECOMMENDATION = "recommendation", "Recommendation"
    INTERNAL = "internal", "Internal"
    AGENCY = "agency", "Agency"