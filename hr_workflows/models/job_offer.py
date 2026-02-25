from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class EmploymentType(models.TextChoices):
    FULL_TIME = 'full_time', 'Full Time'
    PART_TIME = 'part_time', 'Part Time'
    CONTRACT  = 'contract',  'Contract'


class ProbationPeriod(models.TextChoices):
    NONE      = 'none',     'None'
    ONE_MONTH = '1_month',  '1 Month'
    THREE_MONTHS = '3_months', '3 Months'
    SIX_MONTHS   = '6_months', '6 Months'


class JobOffer(models.Model):
    application = models.OneToOneField(
        'hr_workflows.RecruitmentApplication',
        on_delete=models.CASCADE,
        related_name='job_offer',
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name='job_offers_created',
    )

    # Offer details
    salary          = models.DecimalField(max_digits=12, decimal_places=2)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    start_date      = models.DateField()
    branch          = models.ForeignKey(
        'branches.Branch',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='job_offers',
    )
    probation_period = models.CharField(
        max_length=20,
        choices=ProbationPeriod.choices,
        default=ProbationPeriod.THREE_MONTHS,
    )
    offer_expiry_date = models.DateField(null=True, blank=True)
    notes             = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Offer for {self.application}"