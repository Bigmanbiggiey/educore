"""Public write interface for `academics` — docs/modules.md."""

from apps.academics.models import GradingScale, SubjectCatalog
from apps.core.context import bind_institution
from apps.institutions.models import Institution, InstitutionCurriculum


def _validate_curriculum_type(curriculum_type: str) -> None:
    if curriculum_type not in InstitutionCurriculum.CurriculumType.values:
        raise ValueError(f"Unknown curriculum type: {curriculum_type!r}")


def create_grading_scale(
    *, institution: Institution, curriculum_type: str, levels: list | None = None
) -> GradingScale:
    _validate_curriculum_type(curriculum_type)
    with bind_institution(institution):
        return GradingScale.objects.create(
            institution_id=institution.id, curriculum_type=curriculum_type, levels=levels or []
        )


def create_subject(
    *, institution: Institution, curriculum_type: str, name: str, code: str
) -> SubjectCatalog:
    _validate_curriculum_type(curriculum_type)
    with bind_institution(institution):
        return SubjectCatalog.objects.create(
            institution_id=institution.id, curriculum_type=curriculum_type, name=name, code=code
        )
