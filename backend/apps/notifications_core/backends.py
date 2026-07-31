"""Pluggable channel backends — docs/modules.md's "pluggable channel
backends (SMS via e.g. Africa's Talking, Email via SMTP/SES, Push)".

Real provider backends land in Phase 5 (docs/roadmap.md) once
`communication` exists and is actually driving traffic through this app —
not designed speculatively before then. `ConsoleChannelBackend` remains
the default for every channel until a deployment explicitly opts in: it
logs instead of calling a real provider, the same role Django's own
`django.core.mail.backends.console.EmailBackend` plays for local dev.

Backend selection is settings-driven per channel
(`NOTIFICATION_CHANNEL_BACKENDS["sms"]`/`["email"]`/`["push"]`, each an
`env()`-configurable import path — same shape `MPESA_GATEWAY_BACKEND`
already established in `config/settings/base.py`), mirroring the
`AIProvider` ABC + settings-driven toggle docs/roadmap.md Phase 9
describes for `ai_gateway` — the same "swap the implementation without
touching call sites" shape applied to notification delivery.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT_SECONDS = 10


class NotificationDeliveryError(Exception):
    """Raised by any real (non-console) backend on delivery failure — an
    unreachable provider, a rejected recipient, a non-2xx response. The
    caller (`tasks.dispatch_notification`) is what turns this into a
    persisted `status=failed` row rather than a crashed task."""


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


class AfricasTalkingSMSBackend(NotificationChannelBackend):
    """Real SMS delivery via Africa's Talking's messaging API
    (https://developers.africastalking.com/docs/sms/sending) — the
    provider docs/modules.md names explicitly. `subject` is ignored (SMS
    has no concept of one, same reasoning
    `NotificationTemplate.subject_template` already documents for
    SMS/push templates being blank).
    """

    def _base_url(self) -> str:
        if settings.AFRICASTALKING_ENV == "production":
            return "https://api.africastalking.com/version1/messaging"
        return "https://api.sandbox.africastalking.com/version1/messaging"

    def send(self, *, recipient_address: str, subject: str, body: str) -> dict:
        data = {
            "username": settings.AFRICASTALKING_USERNAME,
            "to": recipient_address,
            "message": body,
        }
        if settings.AFRICASTALKING_SENDER_ID:
            data["from"] = settings.AFRICASTALKING_SENDER_ID
        try:
            response = requests.post(
                self._base_url(),
                data=data,
                headers={
                    "apiKey": settings.AFRICASTALKING_API_KEY,
                    "Accept": "application/json",
                },
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise NotificationDeliveryError(f"Africa's Talking request failed: {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise NotificationDeliveryError(
                f"Africa's Talking returned a non-JSON response: {response.text}"
            ) from exc

        recipients = payload.get("SMSMessageData", {}).get("Recipients", [])
        recipient_status = recipients[0].get("status") if recipients else None
        if response.status_code != 201 or recipient_status != "Success":
            raise NotificationDeliveryError(f"Africa's Talking rejected the message: {payload}")
        return payload


class DjangoEmailChannelBackend(NotificationChannelBackend):
    """Real email delivery via Django's own email framework
    (`EMAIL_BACKEND`/`EMAIL_HOST`/etc. in `config/settings/base.py`) — SMTP
    by default, which is also how SES's SMTP interface is consumed
    (docs/modules.md names "SMTP/SES" as one option, not two integrations:
    SES's SMTP endpoint is just another SMTP server from Django's
    perspective, no SES-specific SDK code needed).
    """

    def send(self, *, recipient_address: str, subject: str, body: str) -> dict:
        try:
            sent_count = send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_address],
                fail_silently=False,
            )
        except Exception as exc:
            raise NotificationDeliveryError(f"Email delivery failed: {exc}") from exc
        if sent_count != 1:
            raise NotificationDeliveryError(
                f"Email backend reported {sent_count} messages sent, expected 1"
            )
        return {"backend": "email", "delivered_to": recipient_address}


def get_backend(channel: str) -> NotificationChannelBackend:
    try:
        backend_path = settings.NOTIFICATION_CHANNEL_BACKENDS[channel]
    except KeyError:
        raise ValueError(f"No backend configured for channel {channel!r}") from None
    backend_class = import_string(backend_path)
    return backend_class()
