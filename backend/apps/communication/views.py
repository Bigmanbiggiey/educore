"""API views for `communication` — docs/api-design.md.

`AnnouncementSerializer` marks `published_at`/`status` read-only — they
only ever change via `create` (`CreateAnnouncementSerializer`) or the
dedicated `publish` RPC action, never an overloaded `PATCH`, same
convention `classes_streams.Term.is_current` established.

`MessageThreadViewSet`/`MessageViewSet` are object-scoped to a thread's own
participants — a fail-closed check on top of the permission gate, same
defense-in-depth pattern as `InvoiceViewSet`. `Message` is nested under its
`MessageThread` (`/api/v1/message-threads/<id>/messages/`) — it has no
independent identity outside its parent, the exact shape
`docs/api-design.md` §1 reserves nesting for, hand-rolled the same way
`timetable.PeriodViewSet` already is (no `drf-nested-routers` dependency
for one nested resource).
"""

from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from api.viewsets import TenantScopedModelViewSet
from apps.communication import services
from apps.communication.filters import AnnouncementFilterSet
from apps.communication.models import Announcement, Message, MessageThread, MessageThreadParticipant
from apps.communication.serializers import (
    AnnouncementSerializer,
    CreateAnnouncementSerializer,
    CreateThreadSerializer,
    MessageSerializer,
    MessageThreadSerializer,
)
from apps.permissions.permissions import HasPermission, IsInstitutionMember

_WRITE_ACTIONS = ("update", "partial_update", "destroy")


class AnnouncementViewSet(TenantScopedModelViewSet):
    queryset_model = Announcement
    serializer_class = AnnouncementSerializer
    filterset_class = AnnouncementFilterSet

    def get_permissions(self):
        if self.action in ("create", "publish", *_WRITE_ACTIONS):
            return [IsInstitutionMember(), HasPermission("communication.announcement.manage")()]
        return [IsInstitutionMember(), HasPermission("communication.announcement.view")()]

    def create(self, request, *args, **kwargs):
        serializer = CreateAnnouncementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        announcement = services.create_announcement(
            institution=request.institution,
            created_by_id=request.user.id,
            **serializer.validated_data,
        )
        return Response(AnnouncementSerializer(announcement).data, status=201)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        announcement = self.get_object()
        if announcement.status == Announcement.Status.PUBLISHED:
            raise ValidationError({"detail": ["This announcement is already published."]})
        announcement = services.publish_announcement(
            institution=request.institution, announcement=announcement
        )
        return Response(AnnouncementSerializer(announcement).data)


class MessageThreadViewSet(TenantScopedModelViewSet):
    # list/retrieve/create only — nothing calls for editing or deleting a
    # thread (deleting would cascade every message in it), so neither is
    # exposed.
    http_method_names = ["get", "post", "head", "options"]
    queryset_model = MessageThread
    serializer_class = MessageThreadSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsInstitutionMember(), HasPermission("communication.message.create")()]
        return [IsInstitutionMember()]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.get_base_queryset()
        participant_thread_ids = MessageThreadParticipant.objects.filter(
            user_id=self.request.user.id
        ).values_list("thread_id", flat=True)
        return self.get_base_queryset().filter(id__in=participant_thread_ids)

    def create(self, request, *args, **kwargs):
        serializer = CreateThreadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant_ids = set(serializer.validated_data["participant_user_ids"])
        participant_ids.add(request.user.id)  # the creator is always a participant
        thread = services.create_thread(
            institution=request.institution, participant_user_ids=list(participant_ids)
        )
        return Response(MessageThreadSerializer(thread).data, status=201)


class MessageViewSet(TenantScopedModelViewSet):
    """List/create only — nothing here calls for message editing/deletion
    semantics, so none is invented."""

    queryset_model = Message
    serializer_class = MessageSerializer

    def get_permissions(self):
        return [IsInstitutionMember()]

    def _is_participant(self, thread_id) -> bool:
        return MessageThreadParticipant.objects.filter(
            thread_id=thread_id, user_id=self.request.user.id
        ).exists()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.get_base_queryset()
        thread_id = self.kwargs["thread_pk"]
        if not self._is_participant(thread_id):
            raise PermissionDenied("Not a participant of this thread.")
        return self.get_base_queryset().filter(thread_id=thread_id)

    def create(self, request, *args, **kwargs):
        thread_id = self.kwargs["thread_pk"]
        if not self._is_participant(thread_id):
            raise PermissionDenied("Not a participant of this thread.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = services.send_message(
            institution=request.institution,
            thread=MessageThread.objects.get(id=thread_id),
            sender_id=request.user.id,
            **serializer.validated_data,
        )
        return Response(self.get_serializer(message).data, status=201)
