"""Public write interface for `curriculum_university` — docs/modules.md.

`record_unit_assessment` is the function `UniversityEngine.record_assessment`
delegates to — it resolves a `Semester` from the framework's generic
`term_id` internally (raising `ValueError`, a 400, if none has been
configured yet), same "reference data must exist first" discipline as
every other plugin's recording function. `recompute_gpa_snapshots` is the
real logic behind `tasks.py`'s Celery task — GPA/CGPA need every unit a
student has taken recomputed together, so this only ever runs
administratively, never live per request (docs/database.md §4: "same
rationale as MeanGradeSnapshot").
"""

import datetime
import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError

from apps.core.context import bind_institution
from apps.curriculum_university.models import (
    CourseRegistration,
    Dissertation,
    Faculty,
    GPASnapshot,
    Graduation,
    Programme,
    School,
    Semester,
    Unit,
    UnitAssessment,
    UniversityDepartment,
)
from apps.curriculum_university.selectors import compute_cgpa, compute_gpa
from apps.institutions.models import Institution


def create_faculty(*, institution: Institution, name: str) -> Faculty:
    with bind_institution(institution):
        return Faculty.objects.create(institution_id=institution.id, name=name)


def create_school(*, institution: Institution, faculty: Faculty, name: str) -> School:
    with bind_institution(institution):
        return School.objects.create(institution_id=institution.id, faculty=faculty, name=name)


def create_department(
    *, institution: Institution, school: School, name: str
) -> UniversityDepartment:
    with bind_institution(institution):
        return UniversityDepartment.objects.create(
            institution_id=institution.id, school=school, name=name
        )


def create_programme(
    *,
    institution: Institution,
    department: UniversityDepartment,
    programme_code: str,
    degree_level: str,
    name: str,
) -> Programme:
    with bind_institution(institution):
        return Programme.objects.create(
            institution_id=institution.id,
            department=department,
            programme_code=programme_code,
            degree_level=degree_level,
            name=name,
        )


def create_unit(
    *,
    institution: Institution,
    programme: Programme,
    unit_code: str,
    name: str,
    credit_hours: int,
    semester_offered: int,
) -> Unit:
    with bind_institution(institution):
        return Unit.objects.create(
            institution_id=institution.id,
            programme=programme,
            unit_code=unit_code,
            name=name,
            credit_hours=credit_hours,
            semester_offered=semester_offered,
        )


def create_semester(
    *, institution: Institution, term_id: uuid.UUID, number: int, name: str
) -> Semester:
    with bind_institution(institution):
        return Semester.objects.create(
            institution_id=institution.id, term_id=term_id, number=number, name=name
        )


def create_course_registration(
    *,
    institution: Institution,
    student_id: uuid.UUID,
    unit: Unit,
    semester: Semester,
    status: str = CourseRegistration.Status.ACTIVE,
) -> CourseRegistration:
    with bind_institution(institution):
        return CourseRegistration.objects.create(
            institution_id=institution.id,
            student_id=student_id,
            unit=unit,
            semester=semester,
            status=status,
        )


def create_dissertation(
    *,
    institution: Institution,
    student_id: uuid.UUID,
    supervisor_id: uuid.UUID,
    title: str,
    status: str = Dissertation.Status.PROPOSED,
) -> Dissertation:
    with bind_institution(institution):
        return Dissertation.objects.create(
            institution_id=institution.id,
            student_id=student_id,
            supervisor_id=supervisor_id,
            title=title,
            status=status,
        )


def create_graduation(
    *,
    institution: Institution,
    student_id: uuid.UUID,
    programme: Programme,
    conferred_at: datetime.datetime,
    classification: str = "",
) -> Graduation:
    with bind_institution(institution):
        return Graduation.objects.create(
            institution_id=institution.id,
            student_id=student_id,
            programme=programme,
            conferred_at=conferred_at,
            classification=classification,
        )


def record_unit_assessment(
    *, institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID, details: dict
) -> UnitAssessment:
    try:
        unit_id = details["unit_id"]
        assessment_type = details["assessment_type"]
        raw_score = details["score"]
        raw_max_score = details["max_score"]
    except KeyError as exc:
        raise ValueError(
            f"University unit assessment details missing required key: {exc}"
        ) from None

    if assessment_type not in UnitAssessment.AssessmentType.values:
        raise ValueError(f"Unknown assessment_type: {assessment_type!r}")

    try:
        score = Decimal(str(raw_score))
        max_score = Decimal(str(raw_max_score))
    except Exception as exc:
        raise ValueError("score/max_score must be numeric.") from exc
    if max_score <= 0 or score < 0 or score > max_score:
        raise ValueError("score must be between 0 and max_score, and max_score must be positive.")

    with bind_institution(institution):
        semester = Semester.objects.filter(term_id=term_id).first()
        if semester is None:
            raise ValueError(f"No semester has been configured yet for term {term_id!r}.")

        try:
            unit = Unit.objects.get(id=unit_id)
        except (Unit.DoesNotExist, DjangoValidationError):
            raise ValueError(f"No unit matches id {unit_id!r}.") from None

        assessment, _ = UnitAssessment.objects.update_or_create(
            institution_id=institution.id,
            student_id=student_id,
            unit=unit,
            semester=semester,
            assessment_type=assessment_type,
            defaults={"score": score, "max_score": max_score},
        )
    return assessment


def recompute_gpa_snapshots(
    *, institution: Institution, semester_id: uuid.UUID
) -> list[GPASnapshot]:
    with bind_institution(institution):
        semester = Semester.objects.get(id=semester_id)
        student_ids = list(
            CourseRegistration.objects.filter(semester=semester)
            .values_list("student_id", flat=True)
            .distinct()
        )

    snapshots = []
    for student_id in student_ids:
        gpa = compute_gpa(institution, student_id, semester)
        if gpa is None:
            continue
        cgpa = compute_cgpa(institution, student_id)
        with bind_institution(institution):
            snapshot, _ = GPASnapshot.objects.update_or_create(
                institution_id=institution.id,
                student_id=student_id,
                semester=semester,
                defaults={"gpa": gpa, "cgpa": cgpa if cgpa is not None else gpa},
            )
        snapshots.append(snapshot)
    return snapshots
