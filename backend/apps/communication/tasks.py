"""Celery tasks owned by `communication` — docs/project-structure.md §3.

`publish_due_announcements` is the first real consumer of Celery Beat's
periodic-task schedule (`CELERY_BEAT_SCHEDULE` in
`config/settings/base.py`) — the `celery-beat` service has always been
provisioned in the docker-compose stack (docs/deployment.md §1) but
nothing had registered a periodic task against it until now.
"""

from celery import shared_task
from django.utils import timezone

from apps.communication.models import Announcement
from apps.communication.services import publish_announcement
from apps.core.context import bind_institution
from apps.institutions.models import Institution


@shared_task
def publish_due_announcements() -> None:
    # Institution.objects.all() is a plain, always-safe read — Institution
    # is Layer 0 (the tenancy root itself), not a TenantScopedModel, so no
    # escape hatch is involved. A Beat task has no institution ambiently
    # bound and must check every institution's due announcements, not just
    # one; each institution's own Announcement rows are only ever touched
    # after properly binding it.
    for institution in Institution.objects.all():
        with bind_institution(institution):
            due = list(
                Announcement.objects.filter(
                    status=Announcement.Status.SCHEDULED, published_at__lte=timezone.now()
                )
            )
        for announcement in due:
            publish_announcement(institution=institution, announcement=announcement)
