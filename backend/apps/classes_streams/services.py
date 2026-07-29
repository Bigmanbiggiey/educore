"""Public write interface for `classes_streams` — docs/modules.md. Other
apps mutate this app's state only through these functions, never by
touching apps.classes_streams.models directly (docs/project-structure.md
§3).

Every write binds `institution` for the duration of the call (see
selectors.py's module docstring for why) and explicitly sets
`institution_id` on every created row — `TenantScopedModel`'s manager
requires a bound tenant just to build the queryset `.create()` runs
through, but doesn't infer `institution_id` from that binding, so it's
always passed explicitly too.
"""

import datetime
import uuid

from django.db import transaction

from apps.classes_streams.models import (
    AcademicYear,
    ClassGrade,
    ClassTeacherAssignment,
    Stream,
    Term,
)
from apps.core.context import bind_institution
from apps.institutions.models import Institution, InstitutionCurriculum


def create_academic_year(
    *, institution: Institution, year_label: str, start_date: datetime.date, end_date: datetime.date
) -> AcademicYear:
    with bind_institution(institution):
        return AcademicYear.objects.create(
            institution_id=institution.id,
            year_label=year_label,
            start_date=start_date,
            end_date=end_date,
        )


def create_term(
    *,
    institution: Institution,
    academic_year: AcademicYear,
    name: str,
    start_date: datetime.date,
    end_date: datetime.date,
) -> Term:
    with bind_institution(institution):
        return Term.objects.create(
            institution_id=institution.id,
            academic_year=academic_year,
            name=name,
            start_date=start_date,
            end_date=end_date,
        )


@transaction.atomic
def set_current_term(*, institution: Institution, term: Term) -> Term:
    """Marks `term` current, unsetting whichever term (if any) held that
    flag before — atomic so `term_one_current_per_institution` is never
    transiently violated by two concurrent requests racing to flip it."""
    with bind_institution(institution):
        Term.objects.filter(is_current=True).exclude(pk=term.pk).update(is_current=False)
        term.is_current = True
        term.save(update_fields=["is_current", "updated_at"])
    return term


def create_class_grade(
    *, institution: Institution, term: Term, name: str, curriculum_type: str
) -> ClassGrade:
    if curriculum_type not in InstitutionCurriculum.CurriculumType.values:
        raise ValueError(f"Unknown curriculum type: {curriculum_type!r}")
    with bind_institution(institution):
        return ClassGrade.objects.create(
            institution_id=institution.id, term=term, name=name, curriculum_type=curriculum_type
        )


def create_stream(
    *, institution: Institution, class_grade: ClassGrade, name: str, capacity: int | None = None
) -> Stream:
    with bind_institution(institution):
        return Stream.objects.create(
            institution_id=institution.id, class_grade=class_grade, name=name, capacity=capacity
        )


def assign_class_teacher(
    *,
    institution: Institution,
    class_grade: ClassGrade,
    term: Term,
    staff_id: uuid.UUID,
    stream: Stream | None = None,
) -> ClassTeacherAssignment:
    with bind_institution(institution):
        assignment, _ = ClassTeacherAssignment.objects.update_or_create(
            institution_id=institution.id,
            class_grade=class_grade,
            stream=stream,
            term=term,
            defaults={"staff_id": staff_id},
        )
    return assignment
