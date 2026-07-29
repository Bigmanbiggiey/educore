"""Public read interface for `parents` — docs/modules.md.
`get_children` is a thin pass-through to `students.selectors.get_guardian_children`
— the one sanctioned `parents` → `students` import (docs/modules.md: "reads
guardian links from `students`, doesn't duplicate them"). Kept as its own
function here (rather than callers importing `students.selectors` directly)
so `parents` has one clear, documented seam for anything it later needs to
add on top (e.g. filtering to only children at *this* institution's
portal-visible set), without every caller needing to know the underlying
app.
"""

import uuid

from apps.parents.models import ParentProfile
from apps.students.selectors import get_guardian_children


def get_parent_profile_by_user_id(user_id: uuid.UUID) -> ParentProfile | None:
    return ParentProfile.objects.filter(user_id=user_id).first()


def get_children(parent_user_id: uuid.UUID):
    return get_guardian_children(parent_user_id)
