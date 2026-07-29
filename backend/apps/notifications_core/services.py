"""Public write interface for `notifications_core` — docs/modules.md.
`send` always enqueues via Celery (`tasks.py`) and never sends
synchronously in a request — a slow or unreachable provider must not block
the request that triggered the notification.

Deliberately has no runtime dependency on `accounts` (docs/modules.md fixes
this app's dependencies as `core`, `institutions` only) — `recipient` is
duck-typed rather than an `accounts.User` isinstance check, and the type
hint below is a `TYPE_CHECKING`-only reference, same pattern
`apps.core.context` uses for its own cross-app annotations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from apps.institutions.models import Institution
from apps.notifications_core.models import Channel, NotificationLog
from apps.notifications_core.tasks import dispatch_notification

if TYPE_CHECKING:
    from apps.accounts.models import User


def _resolve_recipient(recipient: "User | str", channel: str) -> tuple["User | None", str]:
    if isinstance(recipient, str):
        return None, recipient

    # Duck-typed rather than `isinstance(recipient, User)` — see module
    # docstring for why this app doesn't import `accounts` at runtime.
    if channel == Channel.EMAIL:
        address = getattr(recipient, "email", None)
    elif channel == Channel.SMS:
        address = getattr(recipient, "phone", None)
    else:
        raise ValueError(
            f"Cannot resolve a {channel!r} address from a user object — accounts.User has no "
            "device-token concept yet; pass a raw address for push."
        )
    if not address:
        raise ValueError(f"{recipient} has no {channel} address on file")
    return recipient, address


def send(
    *,
    institution: Institution,
    recipient: "User | str",
    template_key: str,
    context: dict,
    channel: str,
) -> NotificationLog:
    if channel not in Channel.values:
        raise ValueError(f"Unknown channel: {channel!r}")

    recipient_user, recipient_address = _resolve_recipient(recipient, channel)

    log = NotificationLog.objects.create(
        institution=institution,
        recipient_user=recipient_user,
        recipient_address=recipient_address,
        channel=channel,
        template_key=template_key,
        status=NotificationLog.Status.QUEUED,
    )
    dispatch_notification.delay(str(log.id), context)
    return log
