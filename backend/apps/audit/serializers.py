"""Read-only shape for the platform-staff audit trail (docs/permissions.md
§7's "queryable fact"). `AuditLog` itself is append-only — there is no
write serializer, ever (see `models.py`'s `AuditLogQuerySet`/`save`/
`delete` guards).
"""

from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    target = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "institution",
            "actor",
            "action",
            "target",
            "diff",
            "ip_address",
            "acting_as_admin",
            "created_at",
        ]
        read_only_fields = fields

    def get_target(self, obj: AuditLog) -> str | None:
        if obj.target_content_type is None or obj.target_object_id is None:
            return None
        content_type = obj.target_content_type
        return f"{content_type.app_label}.{content_type.model}#{obj.target_object_id}"
