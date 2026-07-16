"""Layer 0 tenancy-root models — docs/database.md §2, docs/modules.md
(`institutions`). Full field detail is fixed here; this shape doesn't
change later regardless of which isolation tier an institution runs on.
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class Institution(TimeStampedModel):
    """The tenancy root — every tenant-scoped app's `institution_id`
    ultimately refers to a row here. Always lives in the shared `default`
    database regardless of its own isolation tier (docs/multitenancy.md
    §4), so `Domain`/`InstitutionCurriculum`/`AcademicCalendarSettings`
    below use real ForeignKeys to it, not the plain-UUID workaround Layer
    1/2 tables need."""

    class IsolationTier(models.TextChoices):
        SHARED_ROW = "shared_row", "Shared database, row isolation"
        DEDICATED_DB = "dedicated_db", "Dedicated database, shared infrastructure"
        DEDICATED_INFRA = "dedicated_infra", "Dedicated infrastructure"

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    isolation_tier = models.CharField(
        max_length=20, choices=IsolationTier.choices, default=IsolationTier.SHARED_ROW
    )
    # Django DB alias when isolation_tier=dedicated_db (docs/multitenancy.md
    # §5). Empty string, not null, per Django's own guidance against
    # null=True on CharField — enforced non-empty for that tier below.
    db_alias = models.CharField(max_length=100, blank=True, default="")
    timezone = models.CharField(max_length=50, default="Africa/Nairobi")
    logo_url = models.URLField(blank=True, default="")
    primary_color = models.CharField(max_length=20, blank=True, default="")
    favicon_url = models.URLField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        pass

    # A nested `class Meta` can't see `IsolationTier` by bare name — nested
    # class bodies don't inherit the enclosing class's local namespace in
    # Python (only module globals), so `constraints` is assigned here, in
    # Institution's own class body, instead of inside Meta's.
    Meta.constraints = [
        models.CheckConstraint(
            condition=models.Q(isolation_tier__in=IsolationTier.values),
            name="institution_valid_isolation_tier",
        ),
        models.CheckConstraint(
            condition=~models.Q(isolation_tier="dedicated_db") | ~models.Q(db_alias=""),
            name="institution_dedicated_db_requires_db_alias",
        ),
    ]

    def __str__(self) -> str:
        return self.name


class InstitutionCurriculum(TimeStampedModel):
    """M2M-through: an institution may run more than one curriculum
    concurrently (docs/database.md §2) — a primary school teaching CBC in
    lower grades and 8-4-4 in upper grades, for instance."""

    class CurriculumType(models.TextChoices):
        CBC = "cbc", "CBC"
        EIGHT_FOUR_FOUR = "844", "8-4-4"
        BRITISH = "british", "British"
        TVET = "tvet", "TVET"
        UNIVERSITY = "university", "University"

    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="curricula"
    )
    curriculum_type = models.CharField(max_length=20, choices=CurriculumType.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        pass

    # See the comment on Institution.Meta above — same nested-class-scoping
    # reason this is assigned here rather than inside `class Meta` itself.
    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution", "curriculum_type"],
            name="unique_institution_curriculum",
        ),
        models.CheckConstraint(
            condition=models.Q(curriculum_type__in=CurriculumType.values),
            name="institution_curriculum_valid_type",
        ),
    ]

    def __str__(self) -> str:
        return f"{self.institution} — {self.get_curriculum_type_display()}"


class Domain(TimeStampedModel):
    """Subdomain/custom-domain → institution mapping. `TenantMiddleware`
    (docs/multitenancy.md §2) resolves every request's tenant through this
    table via `selectors.get_institution_by_domain`."""

    class DomainType(models.TextChoices):
        SUBDOMAIN = "subdomain", "Subdomain"
        CUSTOM = "custom", "Custom domain"

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="domains")
    hostname = models.CharField(max_length=255, unique=True)
    domain_type = models.CharField(max_length=20, choices=DomainType.choices)
    is_primary = models.BooleanField(default=False)
    # Not in docs/database.md's Domain table, but required to actually
    # implement the TXT-record verification flow it describes
    # (docs/multitenancy.md §6): the token an institution admin publishes
    # at their DNS provider before `services.verify_domain` will succeed.
    verification_token = models.CharField(max_length=64, blank=True, default="")
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        pass

    # See the comment on Institution.Meta above — same nested-class-scoping
    # reason this is assigned here rather than inside `class Meta` itself.
    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution"],
            condition=models.Q(is_primary=True),
            name="one_primary_domain_per_institution",
        ),
        models.CheckConstraint(
            condition=models.Q(domain_type__in=DomainType.values),
            name="domain_valid_type",
        ),
    ]

    def __str__(self) -> str:
        return self.hostname


class AcademicCalendarSettings(TimeStampedModel):
    """Per-institution defaults consumed when `classes_streams` (Phase 2,
    docs/roadmap.md) generates `AcademicYear`/`Term` rows — this model
    doesn't own the calendar entities themselves.

    docs/database.md doesn't fix this model's fields at the field level
    the way it does the rest of Layer 0, so it's kept deliberately minimal
    here rather than guessed in detail.
    """

    institution = models.OneToOneField(
        Institution, on_delete=models.CASCADE, related_name="calendar_settings"
    )
    academic_year_start_month = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    terms_per_year = models.PositiveSmallIntegerField(default=3)

    def __str__(self) -> str:
        return f"{self.institution} calendar settings"
