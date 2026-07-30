"""Public write interface for `curriculum_british` — docs/modules.md.

`record_coursework` is the function `BritishEngine.record_assessment`
delegates to, same role as the other two plugins' assessment-recording
functions. `set_predicted_grade` is `update_or_create`-keyed on
(student, subject, academic_year) — setting the same one twice updates in
place rather than duplicating.
"""

import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError

from apps.core.context import bind_institution
from apps.curriculum_british.models import Coursework, PredictedGrade, Subject, YearGroup
from apps.institutions.models import Institution


def create_year_group(
    *, institution: Institution, class_grade_id: uuid.UUID, key_stage: str, name: str, order: int
) -> YearGroup:
    if key_stage not in YearGroup.KeyStage.values:
        raise ValueError(f"Unknown key_stage: {key_stage!r}")
    with bind_institution(institution):
        return YearGroup.objects.create(
            institution_id=institution.id,
            class_grade_id=class_grade_id,
            key_stage=key_stage,
            name=name,
            order=order,
        )


def create_subject(
    *,
    institution: Institution,
    subject_catalog_id: uuid.UUID,
    name: str,
    code: str,
    qualification_level: str = Subject.QualificationLevel.NONE,
) -> Subject:
    with bind_institution(institution):
        return Subject.objects.create(
            institution_id=institution.id,
            subject_catalog_id=subject_catalog_id,
            name=name,
            code=code,
            qualification_level=qualification_level,
        )


def set_predicted_grade(
    *,
    institution: Institution,
    student_id: uuid.UUID,
    subject: Subject,
    academic_year_id: uuid.UUID,
    predicted_grade: str,
    set_by: uuid.UUID,
) -> PredictedGrade:
    with bind_institution(institution):
        grade, _ = PredictedGrade.objects.update_or_create(
            institution_id=institution.id,
            student_id=student_id,
            subject=subject,
            academic_year_id=academic_year_id,
            defaults={"predicted_grade": predicted_grade, "set_by": set_by},
        )
    return grade


def record_coursework(
    *, institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID, details: dict
) -> Coursework:
    try:
        subject_id = details["subject_id"]
        component = details["component"]
        raw_score = details["score"]
        raw_max_score = details["max_score"]
    except KeyError as exc:
        raise ValueError(f"British coursework details missing required key: {exc}") from None

    try:
        score = Decimal(str(raw_score))
        max_score = Decimal(str(raw_max_score))
    except Exception as exc:
        raise ValueError("score/max_score must be numeric.") from exc
    if max_score <= 0 or score < 0 or score > max_score:
        raise ValueError("score must be between 0 and max_score, and max_score must be positive.")

    with bind_institution(institution):
        try:
            subject = Subject.objects.get(id=subject_id)
        except (Subject.DoesNotExist, DjangoValidationError):
            raise ValueError(f"No subject matches id {subject_id!r}.") from None

        coursework, _ = Coursework.objects.update_or_create(
            institution_id=institution.id,
            student_id=student_id,
            subject=subject,
            term_id=term_id,
            component=component,
            defaults={"score": score, "max_score": max_score},
        )
    return coursework
