"""Base model mixins every Layer 1+ app builds on — docs/modules.md
(`core`) and docs/database.md §1 fix the conventions these encode.
"""

from django.db import models
from django.utils import timezone

from apps.core.context import TenantContextMissing, current_institution
from apps.core.uuid7 import uuid7


class UUIDPrimaryKeyModel(models.Model):
    """Time-ordered UUID PK (docs/database.md §1) instead of a random
    UUIDv4 or Django's default bigint, which fragments Postgres's B-tree
    index under high insert volume."""

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(UUIDPrimaryKeyModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class SoftDeleteModel(models.Model):
    """Standalone soft-delete mixin. Only apply to models where a wrong
    hard-delete is costly or historical reference matters (docs/database.md
    §1) — most tables hard-delete.

    Tenant-scoped models that also need this should use
    `TenantScopedSoftDeleteModel` below instead of combining this class
    with `TenantScopedModel` directly via multiple inheritance: both define
    a default `objects` manager, and Django would resolve the collision via
    MRO rather than actually composing the two behaviors, silently giving
    up either tenant filtering or soft-delete filtering.
    """

    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=["deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)


class TenantQuerySet(models.QuerySet):
    def _scoped(self):
        institution = current_institution.get()
        if institution is None:
            raise TenantContextMissing(
                "No tenant bound — refusing to query a tenant-scoped model "
                "without one. Bind one via TenantMiddleware or "
                "core.context.bind_institution()."
            )
        return self.filter(institution_id=institution.id)


class TenantManager(models.Manager):
    """Auto-filters every query by the bound tenant (docs/multitenancy.md
    §3). Business logic never writes `Model.objects.filter(institution=...)`
    manually — the filtering is structural, not a convention to remember."""

    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)._scoped()

    def none(self):
        # `.none()` never touches real data — Django's EmptyQuerySet
        # short-circuits before any query reaches the DB — so it's safe
        # without a bound tenant. Needed by third-party schema-introspection
        # tooling (drf-spectacular, django-filter) that calls
        # `Model._default_manager.none()` directly outside any real
        # request, bypassing any view-level fix.
        return TenantQuerySet(self.model, using=self._db).none()


class TenantScopedModel(TimeStampedModel):
    """Base for every Layer 1/2 model. Extends `TimeStampedModel`, not
    `UUIDPrimaryKeyModel` directly — docs/database.md §1's `created_at`/
    `updated_at` rule is "not optional per-model", so every tenant-scoped
    model gets them for free rather than each Layer 1+ app remembering to
    add them (or worse, multiple-inheriting `TimeStampedModel` alongside
    this, which would hit the same manager-collision problem
    `TenantScopedSoftDeleteModel` below documents for `SoftDeleteModel`).

    `institution_id` is a plain indexed UUIDField, not a ForeignKey —
    Django cannot enforce FK constraints across the database boundary
    dedicated-DB-tier tenants introduce, so this is applied uniformly
    rather than varying by isolation tier (docs/multitenancy.md §1)."""

    institution_id = models.UUIDField(db_index=True)

    objects = TenantManager()

    # Escape hatch for the small number of platform-level call sites
    # (institution provisioning, act-as sessions, management commands) that
    # need cross-tenant queries. import-linter restricts which apps may
    # reference this (docs/multitenancy.md §3).
    all_tenants_unsafe = models.Manager()

    class Meta:
        abstract = True


class TenantScopedSoftDeleteQuerySet(TenantQuerySet, SoftDeleteQuerySet):
    pass


class TenantScopedSoftDeleteManager(models.Manager):
    def get_queryset(self):
        return TenantScopedSoftDeleteQuerySet(self.model, using=self._db)._scoped().alive()

    def none(self):
        # See TenantManager.none() — same reasoning.
        return TenantScopedSoftDeleteQuerySet(self.model, using=self._db).none()


class TenantScopedAllManager(models.Manager):
    """Tenant-scoped but includes soft-deleted rows — e.g. an institution
    admin viewing withdrawn/archived students."""

    def get_queryset(self):
        return TenantScopedSoftDeleteQuerySet(self.model, using=self._db)._scoped()

    def none(self):
        # See TenantManager.none() — same reasoning.
        return TenantScopedSoftDeleteQuerySet(self.model, using=self._db).none()


class TenantScopedSoftDeleteModel(TenantScopedModel):
    """Convenience base for the models docs/database.md §1 lists as
    soft-deletable (Student, Staff, Invoice, Payment, Enrollment,
    Document) — all of which are tenant-scoped. See `SoftDeleteModel` for
    why this overrides `TenantScopedModel.objects` instead of combining the
    two mixins via plain multiple inheritance."""

    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)

    objects = TenantScopedSoftDeleteManager()
    all_objects = TenantScopedAllManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=["deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)
