"""Layer 1 model — docs/database.md §3, docs/modules.md (`parents`). Not on
docs/database.md §1's soft-deletable list, so plain `TenantScopedModel`.

`user_id` is a plain UUIDField, not a real FK — `accounts.User` is
platform-global and exempt from real FKs from any tenant-scoped model
(docs/database.md §1). This app deliberately does **not** store guardian↔
child links itself — `students.GuardianRelationship` owns those (a guardian
may have no `ParentProfile` at all, e.g. an emergency contact), and
`parents.selectors` reads them via `students.selectors.get_guardian_children`
— the one sanctioned `parents` → `students` import docs/modules.md names.
"""

from django.db import models

from apps.core.models import TenantScopedModel


class ParentProfile(TenantScopedModel):
    user_id = models.UUIDField()
    preferred_language = models.CharField(max_length=10, blank=True, default="en")
    notification_preferences = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    Meta.constraints = [
        models.UniqueConstraint(
            fields=["institution_id", "user_id"],
            name="parentprofile_unique_user_per_institution",
        ),
    ]

    def __str__(self) -> str:
        return f"Parent profile for {self.user_id}"
