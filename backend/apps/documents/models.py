"""Layer 1 models — docs/database.md §3 ("Documents, Communication,
Admissions"):

    Document (institution, category, minio_object_key, content_type_target
              [generic FK], uploaded_by, is_confidential)

Unlike `library`'s `Loan.borrower` (a closed Student|Staff pair, modeled as
a discriminator + UUID to avoid a real generic FK), `Document`'s attach
point is deliberately open-ended — docs/modules.md itself calls it a
"generic-FK attach point", meant to hang off *any* future model, not a
fixed enum. That's exactly what `audit.AuditLog.target` already solved:
a real `django.contrib.contenttypes` `GenericForeignKey`, with
`target_object_id` as a `UUIDField` (not the default `PositiveIntegerField`
`GenericForeignKey` assumes) since every model in this codebase has a UUID
PK. Reused verbatim here rather than re-solving it.

`uploaded_by_id` is a plain cross-app UUID to `accounts.User`, nullable —
system-generated documents (e.g. `reports` storing a generated PDF) have no
human uploader. `Document` is the one model in this app on
docs/database.md §1's soft-delete list ("Student, Staff, Invoice, Payment,
Enrollment, Document"), so it's `TenantScopedSoftDeleteModel`; `category`
is a plain `TenantScopedModel` — it's a lookup table, not a table where a
wrong hard-delete loses anything not already visible on the category name
itself.
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.models import TenantScopedModel, TenantScopedSoftDeleteModel


class DocumentCategory(TenantScopedModel):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Document(TenantScopedSoftDeleteModel):
    # SET_NULL, not CASCADE: a category being deleted shouldn't take every
    # document filed under it down with it — same reasoning as
    # `inventory.Asset.supplier`.
    category = models.ForeignKey(
        DocumentCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="documents"
    )
    minio_object_key = models.CharField(max_length=500)
    target_content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL
    )
    target_object_id = models.UUIDField(null=True, blank=True)
    target = GenericForeignKey("target_content_type", "target_object_id")
    uploaded_by_id = models.UUIDField(null=True, blank=True)
    is_confidential = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    Meta.indexes = [
        models.Index(fields=["target_content_type", "target_object_id"]),
    ]

    def __str__(self) -> str:
        return self.minio_object_key
