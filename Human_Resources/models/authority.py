from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from Human_Resources.models.permission import Permission


class Belt(models.Model):
    """
    Geopolitical authority layer.
    Immutable classification used for HR scoping.
    """

    code = models.CharField(
        max_length=16,
        unique=True,
        help_text="Short immutable code e.g. SOUTH, MIDDLE, NORTH",
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


class AuthorityRole(models.Model):
    """
    System / authority role.
    Defines WHAT someone is allowed to do.
    Scope defines WHERE they can do it.
    """

    SCOPE_GLOBAL = "GLOBAL"
    SCOPE_BELT = "BELT"
    SCOPE_REGION = "REGION"
    SCOPE_BRANCH = "BRANCH"

    SCOPE_CHOICES = (
        (SCOPE_GLOBAL, "Global"),
        (SCOPE_BELT, "Belt"),
        (SCOPE_REGION, "Region"),
        (SCOPE_BRANCH, "Branch"),
    )

    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="authority_roles",
        help_text="Permissions granted by this authority role",
    )

    code = models.CharField(
        max_length=40,
        unique=True,
        help_text="Canonical authority role code e.g. HR_ADMIN, BELT_HR_OVERSEER",
    )

    name = models.CharField(
        max_length=120,
        help_text="Human-readable name",
    )

    description = models.TextField(blank=True)

    allowed_scopes = models.JSONField(
        default=list,
        help_text="Allowed scope types for this role",
    )

    is_system_role = models.BooleanField(
        default=True,
        help_text="System-defined authority role",
    )

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.name


class AuthorityAssignment(models.Model):
    """
    Assigns an authority role to a user within a specific geographic scope.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authority_assignments",
    )

    role = models.ForeignKey(
        AuthorityRole,
        on_delete=models.PROTECT,
        related_name="assignments",
    )

    scope_type = models.CharField(
        max_length=16,
        choices=AuthorityRole.SCOPE_CHOICES,
    )

    belt = models.ForeignKey(
        Belt,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    region = models.ForeignKey(
        "branches.Region",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    branch = models.ForeignKey(
        "branches.Branch",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Enforce allowed scope
        if self.scope_type not in self.role.allowed_scopes:
            raise ValidationError(
                f"Role {self.role.code} cannot be used with scope {self.scope_type}"
            )

        # Enforce exactly one scope target
        if self.scope_type == AuthorityRole.SCOPE_GLOBAL:
            return

        scope_map = {
            AuthorityRole.SCOPE_BELT: self.belt,
            AuthorityRole.SCOPE_REGION: self.region,
            AuthorityRole.SCOPE_BRANCH: self.branch,
        }

        if not scope_map.get(self.scope_type):
            raise ValidationError("Scope target must be set for this role.")

    def __str__(self):
        return f"{self.user} → {self.role.code} ({self.scope_type})"
