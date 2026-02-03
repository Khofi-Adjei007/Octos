from django.db import models


class Belt(models.Model):
    """
    Geopolitical authority layer.
    Immutable classification used for HR scoping.
    """

    code = models.CharField(
        max_length=16,
        unique=True,
        help_text="Short immutable code e.g. SOUTH, MID, NORTH",
    )

    name = models.CharField(
        max_length=100,
        help_text="Human-readable belt name",
    )

    order = models.PositiveSmallIntegerField(
        help_text="Ordering from south to north",
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name
