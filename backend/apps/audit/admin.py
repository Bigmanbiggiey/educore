from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only by design — an editable admin view on a compliance log
    defeats the point of it being append-only (apps.audit.models.AuditLog)."""

    list_display = (
        "created_at",
        "actor",
        "institution",
        "action",
        "target_content_type",
        "ip_address",
    )
    list_filter = ("action", "institution")
    search_fields = ("action", "actor__email", "actor__phone")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
