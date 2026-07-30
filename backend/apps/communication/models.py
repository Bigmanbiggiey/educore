"""Layer 1 models — docs/database.md §"Documents, Communication, Admissions",
docs/modules.md (`communication`).

docs/modules.md's table names this app's owned models as "Announcement,
Circular, MessageThread", but docs/database.md's schema section gives only
one field list — `Announcement (institution, audience[roles/classes], title,
body, published_at)` — no separate Circular fields anywhere. Read the same
way this codebase has repeatedly read an identical shape
(`curriculum_844`'s four exam types, `curriculum_tvet.PracticalAssessment`,
`curriculum_university.UnitAssessment`): one model, a `kind` discriminator,
not two near-identical tables.

`MessageThread`'s "participants[M2M User]" can't be a real Django
`ManyToManyField` to `accounts.User` — this is a `TenantScopedModel` that
can live in a different physical database than `accounts.User` for a
dedicated-DB tenant (docs/multitenancy.md §1), the exact reason every other
cross-app reference to `accounts.User` in this codebase
(`Payment.recorded_by_id`, `GuardianRelationship.guardian_user_id`,
`Student.user_id`) is a plain `UUIDField`, never a real FK. Modeled instead
as a small `MessageThreadParticipant` join model, same shape as
`permissions.MembershipRole`.
"""

from django.db import models

from apps.core.models import TenantScopedModel


class Announcement(TenantScopedModel):
    class Kind(models.TextChoices):
        ANNOUNCEMENT = "announcement", "Announcement"
        CIRCULAR = "circular", "Circular"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SCHEDULED = "scheduled", "Scheduled"
        PUBLISHED = "published", "Published"

    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.ANNOUNCEMENT)
    title = models.CharField(max_length=200)
    body = models.TextField()
    # {"roles": ["Teacher", ...], "class_grade_ids": ["<uuid>", ...]} — too
    # varied per-institution to fix a schema, same call as
    # finance.FeeStructure.line_items.
    audience = models.JSONField(default=dict, blank=True)
    # Channels to fan out through beyond the always-on console/in-app log,
    # e.g. ["sms", "email"] — a plain list, not an enum-backed M2M, since
    # notifications_core.Channel is the single source of truth for valid
    # values and is validated at the service layer, not the DB layer.
    channels = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    # Set when actually published (immediately or by the scheduled-publish
    # task) — not merely when scheduled. Nullable: a DRAFT/SCHEDULED
    # announcement has no publish time yet.
    published_at = models.DateTimeField(null=True, blank=True)
    created_by_id = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.CheckConstraint(
            condition=models.Q(kind__in=Kind.values), name="announcement_valid_kind"
        ),
        models.CheckConstraint(
            condition=models.Q(status__in=Status.values), name="announcement_valid_status"
        ),
    ]

    Meta.indexes = [
        models.Index(fields=["institution_id", "status", "published_at"]),
    ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.title}"


class MessageThread(TenantScopedModel):
    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Thread {self.id}"


class MessageThreadParticipant(TenantScopedModel):
    thread = models.ForeignKey(
        MessageThread, on_delete=models.CASCADE, related_name="thread_participants"
    )
    user_id = models.UUIDField()

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["thread", "user_id"], name="messagethreadparticipant_unique_per_thread_user"
        ),
    ]

    def __str__(self) -> str:
        return f"{self.user_id} — thread {self.thread_id}"


class Message(TenantScopedModel):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name="messages")
    sender_id = models.UUIDField()
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sent_at"]

    def __str__(self) -> str:
        return f"Message {self.id} — thread {self.thread_id}"
