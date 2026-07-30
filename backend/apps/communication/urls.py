from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.communication.views import AnnouncementViewSet, MessageThreadViewSet, MessageViewSet

app_name = "communication"

router = DefaultRouter()
router.register("announcements", AnnouncementViewSet, basename="announcement")
router.register("message-threads", MessageThreadViewSet, basename="message-thread")

_message_list = MessageViewSet.as_view({"get": "list", "post": "create"})

urlpatterns = [
    *router.urls,
    path(
        "message-threads/<uuid:thread_pk>/messages/", _message_list, name="message-thread-messages"
    ),
]
