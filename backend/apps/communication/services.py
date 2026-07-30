"""Public write interface for `communication` — docs/modules.md.

`publish_announcement` is the exact contract docs/modules.md names:
"`services.publish_announcement(...)` calls `notifications_core.services.send(...)`
per recipient." Every write here binds `institution` for the duration of
the call (`apps.core.context.bind_institution`), same convention as every
other Layer 1 app's services.py.

Resolving an Announcement's `audience` into real recipients needs actual
`accounts.User` objects (not just UUIDs) — `notifications_core.services.send`
duck-types its `recipient` argument via `getattr(recipient, "email"/"phone")`
rather than accepting a raw address for a known user, and passing the real
object is what lets `NotificationLog.recipient_user` actually resolve
(docs/notifications_core's own `_resolve_recipient`). `accounts` is Layer 0,
always a permitted Layer 1 dependency (docs/multitenancy.md §4: identity
always lives in the shared `default` database, so a plain read never
crosses a dedicated-DB tenant boundary) — this is simply the first Layer 1
app to actually exercise it for this purpose.
"""

import logging
import uuid

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.communication.models import Announcement, Message, MessageThread, MessageThreadParticipant
from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.notifications_core import services as notifications_core_services
from apps.permissions.selectors import get_members_with_role
from apps.students.selectors import get_guardians_for_class

logger = logging.getLogger(__name__)

ANNOUNCEMENT_TEMPLATE_KEY = "communication.announcement.published"


def create_announcement(
    *,
    institution: Institution,
    kind: str,
    title: str,
    body: str,
    audience: dict,
    channels: list[str],
    created_by_id: uuid.UUID | None,
    published_at=None,
) -> Announcement:
    """`status` is derived from `published_at`: no value means a draft,
    a future value means scheduled (the Beat-scheduled
    `tasks.publish_due_announcements` picks it up later), anything else
    publishes immediately, inline, in the same call."""
    now = timezone.now()
    if published_at is None:
        status = Announcement.Status.DRAFT
    elif published_at > now:
        status = Announcement.Status.SCHEDULED
    else:
        status = Announcement.Status.PUBLISHED

    with bind_institution(institution):
        announcement = Announcement.objects.create(
            institution_id=institution.id,
            kind=kind,
            title=title,
            body=body,
            audience=audience,
            channels=channels,
            status=status,
            published_at=published_at if status != Announcement.Status.PUBLISHED else now,
            created_by_id=created_by_id,
        )
    if status == Announcement.Status.PUBLISHED:
        publish_announcement(institution=institution, announcement=announcement)
    return announcement


def _resolve_audience(institution: Institution, audience: dict) -> list[User]:
    recipient_ids: set[uuid.UUID] = set()
    for role_name in audience.get("roles", []):
        recipient_ids.update(
            get_members_with_role(institution, role_name).values_list("id", flat=True)
        )
    for class_grade_id in audience.get("class_grade_ids", []):
        recipient_ids.update(get_guardians_for_class(institution, class_grade_id))
    return list(User.objects.filter(id__in=recipient_ids))


@transaction.atomic
def publish_announcement(*, institution: Institution, announcement: Announcement) -> Announcement:
    recipients = _resolve_audience(institution, announcement.audience)
    for recipient in recipients:
        for channel in announcement.channels:
            try:
                notifications_core_services.send(
                    institution=institution,
                    recipient=recipient,
                    template_key=ANNOUNCEMENT_TEMPLATE_KEY,
                    context={"title": announcement.title, "body": announcement.body},
                    channel=channel,
                )
            except ValueError:
                # notifications_core.services.send raises when this
                # specific recipient has no address on file for this one
                # channel (e.g. a guardian with no phone on record for an
                # SMS-targeted announcement) — real and expected in normal
                # use, not a reason to abort the whole fan-out for every
                # other recipient/channel.
                logger.warning(
                    "Skipping %s notification for recipient %s — no address on file",
                    channel,
                    recipient.id,
                )

    with bind_institution(institution):
        announcement.status = Announcement.Status.PUBLISHED
        announcement.published_at = timezone.now()
        announcement.save(update_fields=["status", "published_at", "updated_at"])
    return announcement


def create_thread(
    *, institution: Institution, participant_user_ids: list[uuid.UUID]
) -> MessageThread:
    with bind_institution(institution):
        thread = MessageThread.objects.create(institution_id=institution.id)
        MessageThreadParticipant.objects.bulk_create(
            MessageThreadParticipant(
                institution_id=institution.id, thread=thread, user_id=user_id
            )
            for user_id in set(participant_user_ids)
        )
    return thread


def send_message(
    *, institution: Institution, thread: MessageThread, sender_id: uuid.UUID, body: str
) -> Message:
    with bind_institution(institution):
        return Message.objects.create(
            institution_id=institution.id, thread=thread, sender_id=sender_id, body=body
        )
