"""Public read interface for `academics` — docs/modules.md.

`get_curriculum_engine` resolves through two steps: which curricula this
*institution* actually runs (`institutions.InstitutionCurriculum`, the
Layer 0 M2M-through — an institution may run several concurrently), then
`registry.resolve(...)` for the concrete plugin (`docs/modules.md`'s Layer
2 inversion — `academics` never imports a `curriculum_*` app directly, only
through the registry each plugin registers itself into).
"""

import uuid

from apps.academics import registry
from apps.academics.models import GradingScale, SubjectCatalog
from apps.classes_streams.selectors import get_class_grade
from apps.institutions.models import Institution, InstitutionCurriculum
from apps.students.models import Student
from apps.students.selectors import get_active_enrollment


def get_grading_scale(institution: Institution, curriculum_type: str) -> GradingScale | None:
    return GradingScale.objects.filter(curriculum_type=curriculum_type).first()


def get_subject_catalog(institution: Institution, curriculum_type: str | None = None):
    queryset = SubjectCatalog.objects.all()
    if curriculum_type is not None:
        queryset = queryset.filter(curriculum_type=curriculum_type)
    return queryset


def get_curriculum_engine(institution: Institution, curriculum_type: str | None = None):
    active = list(
        InstitutionCurriculum.objects.filter(institution=institution, is_active=True).values_list(
            "curriculum_type", flat=True
        )
    )
    if curriculum_type is None:
        if len(active) != 1:
            raise ValueError(
                f"institution={institution.id!r} runs {len(active)} active curricula; "
                "curriculum_type must be specified explicitly."
            )
        curriculum_type = active[0]
    elif curriculum_type not in active:
        raise ValueError(
            f"institution={institution.id!r} does not have curriculum_type={curriculum_type!r} "
            "active."
        )
    return registry.resolve(curriculum_type)


def get_curriculum_type_for_student(
    institution: Institution, student: Student, term_id: uuid.UUID
) -> str | None:
    """Resolves which curriculum a student's *current enrollment* falls
    under — the server-side lookup the generic assessment/report-card
    endpoints use so a client never has to know or pass curriculum_type
    itself (docs/api-design.md §8)."""
    enrollment = get_active_enrollment(student, term_id)
    if enrollment is None:
        return None
    class_grade = get_class_grade(institution, enrollment.class_grade_id)
    return class_grade.curriculum_type if class_grade else None
