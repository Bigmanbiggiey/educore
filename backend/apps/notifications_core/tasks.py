"""Celery tasks owned by `notifications_core` — docs/project-structure.md
§3. `dispatch_notification` is the only consumer of `services.send`'s
enqueue call; it does the actual template render + provider dispatch, off
the request/response cycle.
"""

import logging
from string import Template

from celery import shared_task

from apps.notifications_core.backends import get_backend
from apps.notifications_core.models import NotificationLog
from apps.notifications_core.selectors import get_template

logger = logging.getLogger(__name__)


@shared_task
def dispatch_notification(notification_log_id: str, context: dict) -> None:
    log = NotificationLog.objects.select_related("institution").get(id=notification_log_id)
    try:
        template = get_template(log.institution, log.template_key, log.channel)
        # string.Template's $identifier substitution only, never str.format —
        # a context dict influenced by end-user input must not be able to
        # reach attribute/method access via a crafted key (docs/coding-standards.md:
        # "sanitize input", "validate everything").
        subject = Template(template.subject_template).safe_substitute(context)
        body = Template(template.body_template).safe_substitute(context)
        backend = get_backend(log.channel)
        response = backend.send(
            recipient_address=log.recipient_address, subject=subject, body=body
        )
    except Exception as exc:
        # The task boundary is where any delivery failure (bad template,
        # unreachable provider, misconfigured backend) becomes a persisted
        # `status=failed` row rather than a silently retried/crashed task —
        # NotificationChannelBackend.send is documented to raise on failure.
        logger.exception("notification dispatch failed for %s", notification_log_id)
        log.status = NotificationLog.Status.FAILED
        log.provider_response = {"error": str(exc)}
    else:
        log.status = NotificationLog.Status.SENT
        log.provider_response = response
    log.save(update_fields=["status", "provider_response", "updated_at"])
