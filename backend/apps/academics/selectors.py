"""Public read interface for `academics` — docs/modules.md.

`get_curriculum_engine` is a genuine stub, not a placeholder pretending to
work: no `curriculum_*` plugin registry exists until Phase 3
(docs/roadmap.md — "Curriculum registry + plugin loader" is a Phase 3
deliverable), so there is nothing to resolve to yet. It raises rather than
silently returning `None`, matching this codebase's own "fail loudly, not
silently" convention (e.g. `TenantContextMissing`) — a caller mistakenly
invoking this before Phase 3 should see exactly why, not a confusing
downstream `AttributeError` on `None`.
"""

from apps.academics.models import GradingScale, SubjectCatalog
from apps.institutions.models import Institution


def get_grading_scale(institution: Institution, curriculum_type: str) -> GradingScale | None:
    return GradingScale.objects.filter(curriculum_type=curriculum_type).first()


def get_subject_catalog(institution: Institution, curriculum_type: str | None = None):
    queryset = SubjectCatalog.objects.all()
    if curriculum_type is not None:
        queryset = queryset.filter(curriculum_type=curriculum_type)
    return queryset


def get_curriculum_engine(institution: Institution, curriculum_type: str | None = None):
    raise NotImplementedError(
        "No curriculum plugin registry exists yet (docs/roadmap.md Phase 3) — "
        f"cannot resolve a curriculum engine for institution={institution.id!r} "
        f"curriculum_type={curriculum_type!r}."
    )
