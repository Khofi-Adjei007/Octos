from django.db import models


class Role(models.Model):
    """
    Job role / position.
    Used for permission mapping and organizational structure.
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=40, unique=True)  # e.g. BRANCH_MGR
    description = models.TextField(blank=True, null=True)
    default_pay_grade = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
