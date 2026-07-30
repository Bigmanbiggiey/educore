"""Request/response shapes for `communication`'s API surface — docs/api-design.md."""

from rest_framework import serializers

from api.serializers import TenantScopedModelSerializer
from apps.communication.models import Announcement, Message, MessageThread


class AnnouncementSerializer(TenantScopedModelSerializer):
    """`published_at`/`status` are read-only here — they only ever change
    via `create` (see `CreateAnnouncementSerializer`) or the dedicated
    `publish` RPC action, never an overloaded `PATCH`, same convention
    `classes_streams.Term.is_current` established."""

    class Meta:
        model = Announcement
        fields = [
            "id",
            "kind",
            "title",
            "body",
            "audience",
            "channels",
            "status",
            "published_at",
            "created_by_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "published_at",
            "created_by_id",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "audience": {
                "help_text": 'e.g. {"roles": ["Teacher"], "class_grade_ids": ["<uuid>"]}'
            },
            "channels": {"help_text": 'Channel keys to fan out through, e.g. ["sms", "email"].'},
        }


class CreateAnnouncementSerializer(serializers.Serializer):
    """Input-only shape for `AnnouncementViewSet.create` — `published_at`
    is writable here (unlike `AnnouncementSerializer`, used for every other
    action) since it's the one moment a client legitimately sets it: omit
    for a draft, a future value to schedule, anything else to publish
    immediately (`services.create_announcement`)."""

    kind = serializers.ChoiceField(choices=Announcement.Kind.choices)
    title = serializers.CharField(max_length=200)
    body = serializers.CharField()
    audience = serializers.DictField(default=dict)
    channels = serializers.ListField(child=serializers.CharField(), default=list)
    published_at = serializers.DateTimeField(required=False, allow_null=True)


class CreateThreadSerializer(serializers.Serializer):
    participant_user_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)


class MessageThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageThread
        fields = ["id", "created_at", "updated_at"]
        read_only_fields = fields


class MessageSerializer(TenantScopedModelSerializer):
    """`thread` is deliberately not a field here — resolved from the nested
    URL (`/api/v1/message-threads/<id>/messages/`), never client-supplied,
    same reasoning `timetable.PeriodSerializer` gives for excluding
    `timetable`."""

    class Meta:
        model = Message
        fields = ["id", "sender_id", "body", "sent_at"]
        read_only_fields = ["id", "sender_id", "sent_at"]
