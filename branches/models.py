from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class Country(models.Model):
    code = models.CharField(max_length=8, unique=True)  # e.g. 'GH'
    name = models.CharField(max_length=100, unique=True)
    currency = models.CharField(max_length=20, blank=True, null=True)
    timezone = models.CharField(max_length=64, default='Africa/Accra', blank=True, null=True)
    meta = models.JSONField(default=dict, blank=True)  # extra country-specific metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Region(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='regions')
    code = models.CharField(max_length=16, blank=True, null=True)  # e.g. 'GA' or 'BR'
    name = models.CharField(max_length=120)
    hr_manager = models.OneToOneField(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hr_region'
    )
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('country', 'name'),)
        ordering = ['name']

    def __str__(self):
        return f"{self.name} — {self.country.code}"


class City(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='cities')
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=32, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('region', 'name'),)
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.region.name}"


class District(models.Model):
    # municipal / district level
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='districts')
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=32, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('city', 'name'),)
        ordering = ['name']

    def __str__(self):
        return f"{self.name} — {self.city.name}"


class Location(models.Model):
    """
    Generic hierarchical administrative unit for future countries.
    Use Location.type to describe level (e.g., 'country','region','state','county','city','district').
    Parent is optional for top-level nodes (country).
    """
    name = models.CharField(max_length=150)
    type = models.CharField(max_length=50, help_text="Administrative level name (e.g. region, city, district)")
    code = models.CharField(max_length=64, blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    timezone = models.CharField(max_length=64, blank=True, null=True)
    meta = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['type', 'name']),
        ]
        ordering = ['type', 'name']

    def __str__(self):
        return f"{self.name} ({self.type})"


class Branch(models.Model):
    """
    Branch model with geographic, capability and contact fields.
    """
    code = models.CharField(max_length=32, unique=True)  # short id like 'FPP-MAIN' or 'TNT-04D'
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True, db_index=True)

    # canonical location links (Ghana-first)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='branches')
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='branches')
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='branches', null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name='branches', null=True, blank=True)

    # flexible location pointer for other countries or non-standard hierarchies
    location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, blank=True, related_name='branches')

    # manager / contact
    manager = models.OneToOneField(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_branch'
    )
    contact_person = models.CharField(max_length=120, blank=True, null=True)
    phone = models.CharField(max_length=24, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # geolocation for routing / distance
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # capabilities & operations
    opening_hours = models.JSONField(default=dict, blank=True)  # simple structure or more advanced later
    is_main = models.BooleanField(default=False)  # HQ flag (enforce uniqueness via app logic)
    is_active = models.BooleanField(default=True)

    # operational metrics
    distance_from_main_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # metadata & audit
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['country', 'region']),
            models.Index(fields=['is_active']),
        ]
        ordering = ['name']
        verbose_name = "Branch"

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        # auto-generate slug
        if not self.slug:
            base = self.code or self.name
            self.slug = slugify(base)[:140]
        super().save(*args, **kwargs)

    def clean(self):
        # enforce that if is_main=True then only one main per country (soft enforcement here)
        if self.is_main:
            qs = Branch.objects.filter(country=self.country, is_main=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise models.ValidationError("Only one main branch is allowed per country. Unset other branch' is_main first.")
