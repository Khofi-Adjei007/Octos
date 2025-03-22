from django.db import models


# equipment/models.py
from django.db import models

class Equipment(models.Model):
    name = models.CharField(max_length=100)
    branch = models.ForeignKey('branches.Branch', on_delete=models.CASCADE, related_name='equipment')
    serial_number = models.CharField(max_length=50, unique=True)
    purchase_date = models.DateField(null=True, blank=True)
    last_maintenance = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name