"""Public read interface for `notifications_core` — docs/modules.md."""

from apps.institutions.models import Institution
from apps.notifications_core.models import NotificationTemplate


def get_template(
    institution: Institution, key: str, channel: str
) -> NotificationTemplate:
    """An institution-specific override takes precedence over the platform
    default (`institution=None`) for the same `(key, channel)`."""
    template = NotificationTemplate.objects.filter(
        institution=institution, key=key, channel=channel
    ).first()
    if template is not None:
        return template

    template = NotificationTemplate.objects.filter(
        institution__isnull=True, key=key, channel=channel
    ).first()
    if template is not None:
        return template

    raise NotificationTemplate.DoesNotExist(
        f"No template for key={key!r} channel={channel!r} "
        f"(checked institution={institution!r} and the platform default)"
    )
