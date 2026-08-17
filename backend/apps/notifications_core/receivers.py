"""Connects `core.signals.notification_requested` to `services.send` — the
sanctioned way a Layer 0 sibling that can't import `notifications_core`
directly (e.g. `apps.permissions`, per `.importlinter`'s independent-
siblings contract) triggers a notification. Wired in `apps.py.ready()`,
same pattern as `apps.audit.receivers`.
"""

from django.dispatch import receiver

from apps.core.signals import notification_requested
from apps.notifications_core.services import send


@receiver(notification_requested)
def handle_notification_requested(
    sender, *, institution, recipient, template_key, context, channel, **kwargs
):
    send(
        institution=institution,
        recipient=recipient,
        template_key=template_key,
        context=context,
        channel=channel,
    )
