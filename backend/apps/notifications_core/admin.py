from django.contrib import admin

from apps.notifications_core.models import NotificationLog, NotificationTemplate


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ("key", "channel", "institution")
    list_filter = ("channel",)
    search_fields = ("key",)


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "institution",
        "recipient_address",
        "channel",
        "template_key",
        "status",
    )
    list_filter = ("status", "channel", "institution")
    search_fields = ("recipient_address", "template_key")
    readonly_fields = ("provider_response", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False
