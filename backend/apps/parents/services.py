"""Public write interface for `parents` — docs/modules.md."""

import uuid

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.parents.models import ParentProfile


def create_parent_profile(
    *,
    institution: Institution,
    user_id: uuid.UUID,
    preferred_language: str = "en",
    notification_preferences: dict | None = None,
) -> ParentProfile:
    with bind_institution(institution):
        return ParentProfile.objects.create(
            institution_id=institution.id,
            user_id=user_id,
            preferred_language=preferred_language,
            notification_preferences=notification_preferences or {},
        )


def update_notification_preferences(
    *, institution: Institution, profile: ParentProfile, preferences: dict
) -> ParentProfile:
    with bind_institution(institution):
        profile.notification_preferences = preferences
        profile.save(update_fields=["notification_preferences", "updated_at"])
    return profile
