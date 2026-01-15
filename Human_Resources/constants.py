# human_resources/constants.py

from django.db import models


class ApplicationSource(models.TextChoices):
    PUBLIC = "public", "Public Application"
    MANAGER = "manager", "Branch Manager Recommendation"


class ApplicationStatus(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    SCREENING = "screening", "Screening"
    INTERVIEW = "interview", "Interview"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    ONBOARDED = "onboarded", "Onboarded"
