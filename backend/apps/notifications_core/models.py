"""Layer 0 channel-agnostic dispatch models — docs/database.md §2,
docs/modules.md (`notifications_core`). Nothing here knows about "fee
reminder" or "exam results" — that's `communication`'s (Layer 1) job; this
app only owns the template/log/delivery plumbing every notification rides
on. `institution`/`recipient_user` use real ForeignKeys, not the
plain-UUID `TenantScopedModel` pattern — like `permissions`/`audit`, this
Layer 0 data always lives in the shared `default` database
(docs/multitenancy.md §4).
"""

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.institutions.models import Institution


class Channel(models.TextChoices):
    SMS = "sms", "SMS"
    EMAIL = "email", "Email"
    PUSH = "push", "Push"


class NotificationTemplate(TimeStampedModel):
    """`institution=None` is the platform default for a given
    `(key, channel)`; an institution may override it with its own row of
    the same `(key, channel)` (docs/database.md §2) — same global/override
    shape as `permissions.Role`, resolved by `selectors.get_template`."""

    institution = models.ForeignKey(
        Institution,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notification_templates",
    )
    key = models.CharField(max_length=100)
    channel = models.CharField(max_length=10, choices=Channel.choices)
    # Not every channel uses a subject (SMS/push don't) — blank, not
    # nullable, per this codebase's CharField/TextField convention for
    # "unset" (docs/database.md §1's own db_alias/totp_secret precedent).
    subject_template = models.TextField(blank=True, default="")
    body_template = models.TextField()

    class Meta:
        pass

    # A nested `class Meta` can't see local names from the enclosing class
    # body (only module globals), so `constraints` is assigned here instead
    # of inside `Meta` itself — same pattern used throughout Layer 0.
    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution", "key", "channel"],
            name="notiftemplate_unique_per_institution",
        ),
        # Postgres treats NULLs as distinct in the constraint above, so it
        # alone wouldn't stop two platform-default (institution IS NULL)
        # rows sharing a (key, channel) — mirrors permissions.Role's
        # role_unique_global_name partial index.
        models.UniqueConstraint(
            fields=["key", "channel"],
            condition=models.Q(institution__isnull=True),
            name="notiftemplate_unique_platform_default",
        ),
        models.CheckConstraint(
            condition=models.Q(channel__in=Channel.values), name="notiftemplate_valid_channel"
        ),
    ]

    def __str__(self) -> str:
        scope = "platform default" if self.institution_id is None else str(self.institution)
        return f"{self.key} ({self.channel}) — {scope}"


class NotificationLog(TimeStampedModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"

    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="notification_logs"
    )
    # Nullable to support sending to a raw guardian phone/email not yet on
    # the platform (docs/database.md §2) — `recipient_address` is always
    # populated regardless.
    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notification_logs",
    )
    recipient_address = models.CharField(max_length=255)
    channel = models.CharField(max_length=10, choices=Channel.choices)
    template_key = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.QUEUED
    )
    provider_response = models.JSONField(default=dict, blank=True)

    class Meta:
        pass

    Meta.indexes = [
        models.Index(fields=["institution", "created_at"]),
        models.Index(fields=["recipient_user", "created_at"]),
    ]
    Meta.constraints = [
        models.CheckConstraint(
            condition=models.Q(channel__in=Channel.values), name="notiflog_valid_channel"
        ),
        models.CheckConstraint(
            condition=models.Q(status__in=Status.values), name="notiflog_valid_status"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.template_key} → {self.recipient_address} ({self.status})"
