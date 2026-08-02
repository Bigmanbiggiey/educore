"""Request/response shapes for `documents`'s API surface — docs/api-design.md.
`target_content_type`/`target_object_id` are exposed as plain writable
fields (the raw `ContentType` PK + a UUID) rather than resolved into a
nested "target" representation — DRF has no built-in generic-relation
serializer, and this project doesn't invent one for a single field pair;
a client that wants to attach a document supplies both values directly,
same as `library.LoanSerializer` exposes `borrower_type`/`borrower_id`
as plain fields instead of a resolved borrower object.
"""

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from api.serializers import TenantScopedModelSerializer
from apps.documents.models import Document, DocumentCategory


class DocumentCategorySerializer(TenantScopedModelSerializer):
    class Meta:
        model = DocumentCategory
        fields = ["id", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DocumentSerializer(TenantScopedModelSerializer):
    target_content_type = serializers.PrimaryKeyRelatedField(queryset=ContentType.objects.all())

    class Meta:
        model = Document
        fields = [
            "id",
            "category",
            "minio_object_key",
            "target_content_type",
            "target_object_id",
            "uploaded_by_id",
            "is_confidential",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "uploaded_by_id": {"help_text": "accounts.User.id of the uploader, if any."},
        }
