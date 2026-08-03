"""Layer 0 compliance model — docs/database.md §2, docs/modules.md
(`audit`). Append-only by design: no `updated_at`, no soft delete, rows are
never mutated — a compliance log that could be edited after the fact isn't
one. `institution`/`actor` use real ForeignKeys, not the plain-UUID
`TenantScopedModel` pattern — like `permissions`'s models, this Layer 0
data always lives in the shared `default` database (docs/multitenancy.md
§4), so the cross-database FK problem doesn't apply.
"""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.models import UUIDPrimaryKeyModel
from apps.institutions.models import Institution


class AuditLogQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValueError("AuditLog rows are append-only and cannot be updated")

    def delete(self):
        raise ValueError("AuditLog rows are append-only and cannot be deleted")


class AuditLog(UUIDPrimaryKeyModel):
    # Nullable: platform-level actions (e.g. System Admin provisioning a
    # tenant) have no institution to attach to (docs/database.md §2).
    institution = models.ForeignKey(
        Institution,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    # Nullable: system/Celery-initiated actions have no human actor.
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=150)
    # docs/permissions.md §7: a first-class, directly queryable column, not
    # buried in `diff` — the explicit point of the break-glass design is
    # turning "was this action taken under an elevated System Admin
    # session" into a queryable fact, not something you have to parse out.
    acting_as_admin = models.BooleanField(default=False)
    # UUIDField, not the PositiveIntegerField GenericForeignKey defaults to
    # assuming — every model in this codebase has a UUID PK
    # (apps.core.models.UUIDPrimaryKeyModel), so target_object_id must match.
    target_content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL
    )
    target_object_id = models.UUIDField(null=True, blank=True)
    target = GenericForeignKey("target_content_type", "target_object_id")
    diff = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = AuditLogQuerySet.as_manager()

    class Meta:
        pass

    # A nested `class Meta` can't see local names from the enclosing class
    # body (only module globals), so `indexes` is assigned here instead of
    # inside `Meta` itself — same pattern as apps.institutions.models.
    Meta.indexes = [
        models.Index(fields=["institution", "created_at"]),
        models.Index(fields=["actor", "created_at"]),
        models.Index(fields=["target_content_type", "target_object_id"]),
    ]

    def __str__(self) -> str:
        return f"{self.action} @ {self.created_at}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("AuditLog rows are append-only and cannot be updated")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditLog rows are append-only and cannot be deleted")
