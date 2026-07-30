from django.contrib import admin

from apps.communication.models import Announcement, Message, MessageThread, MessageThreadParticipant


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "institution_id", "status", "published_at")
    list_filter = ("kind", "status")


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ("id", "institution_id", "created_at")


@admin.register(MessageThreadParticipant)
class MessageThreadParticipantAdmin(admin.ModelAdmin):
    list_display = ("thread", "user_id")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("thread", "sender_id", "sent_at")
