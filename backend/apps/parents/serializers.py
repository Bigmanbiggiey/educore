from api.serializers import TenantScopedModelSerializer
from apps.parents.models import ParentProfile


class ParentProfileSerializer(TenantScopedModelSerializer):
    class Meta:
        model = ParentProfile
        fields = [
            "id",
            "user_id",
            "preferred_language",
            "notification_preferences",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "user_id": {"help_text": "This parent's login (accounts.User)."},
            "preferred_language": {
                "help_text": "Language code for portal/notification content.",
                "required": False,
            },
            "notification_preferences": {
                "help_text": "Per-channel notification opt-in/out settings.",
                "required": False,
            },
        }
