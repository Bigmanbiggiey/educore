"""Pluggable channel backends — docs/modules.md's "pluggable channel
backends (SMS via e.g. Africa's Talking, Email via SMTP/SES, Push)".

Real provider backends (Africa's Talking, SES/SMTP, a push provider) land
in Phase 5 (docs/roadmap.md) once `communication` exists and is actually
driving traffic through this app — not designed speculatively now. Until
then, `ConsoleChannelBackend` is the settings-configured default for every
channel: it logs instead of calling a real provider, the same role
Django's own `django.core.mail.backends.console.EmailBackend` plays for
local dev.

Backend selection is settings-driven (`NOTIFICATION_CHANNEL_BACKENDS`),
mirroring the `AIProvider` ABC + settings-driven toggle docs/roadmap.md
Phase 9 describes for `ai_gateway` — the same "swap the implementation
without touching call sites" shape applied to notification delivery.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


class NotificationChannelBackend(ABC):
    @abstractmethod
    def send(self, *, recipient_address: str, subject: str, body: str) -> dict:
        """Sends the message and returns a JSON-serializable provider
        response, persisted verbatim to `NotificationLog.provider_response`.
        Raises on delivery failure — the caller (`tasks.dispatch_notification`)
        is what translates that into a `status=failed` log row."""


class ConsoleChannelBackend(NotificationChannelBackend):
    def send(self, *, recipient_address: str, subject: str, body: str) -> dict:
        logger.info(
            "notification (console backend): to=%s subject=%r body=%r",
            recipient_address,
            subject,
            body,
        )
        return {"backend": "console", "delivered_to": recipient_address}


def get_backend(channel: str) -> NotificationChannelBackend:
    try:
        backend_path = settings.NOTIFICATION_CHANNEL_BACKENDS[channel]
    except KeyError:
        raise ValueError(f"No backend configured for channel {channel!r}") from None
    backend_class = import_string(backend_path)
    return backend_class()
