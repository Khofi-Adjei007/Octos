from django.db import models


# branches/models.py
from django.db import models

class Region(models.Model):
    name = models.CharField(max_length=100, unique=True)  # e.g., "Greater Accra Region"
    hr_manager = models.OneToOneField(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hr_region'
    )  # One HR manager per region

    def __str__(self):
        return self.name


class Branch(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., "FPP-Main"
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='branches')
    manager = models.OneToOneField(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_branch'
    )  # One manager per branch
    address = models.TextField()
    distance_from_main = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    is_main = models.BooleanField(default=False)
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.name