"""Public read interface for `curriculum_university` — docs/modules.md.

`get_semester_for_term`/GPA-related functions self-bind (explicit
`institution` argument), same shape `curriculum_844`/`curriculum_british`'s
equivalents use — GPA computation in particular is documented to also run
from a Celery task with nothing ambiently bound.
"""

import uuid
from decimal import Decimal

from apps.academics.selectors import get_grading_scale
from apps.core.context import bind_institution
from apps.curriculum_university.models import (
    CourseRegistration,
    Dissertation,
    GPASnapshot,
    Graduation,
    Semester,
    UnitAssessment,
)
from apps.institutions.models import Institution, InstitutionCurriculum
from apps.students.selectors import get_student_by_id


def get_semester_for_term(institution: Institution, term_id: uuid.UUID) -> Semester | None:
    with bind_institution(institution):
        return Semester.objects.filter(term_id=term_id).first()


def get_registrations(institution: Institution, student_id: uuid.UUID, semester: Semester):
    return CourseRegistration.objects.filter(
        student_id=student_id, semester=semester
    ).select_related("unit")


def get_unit_assessments(institution: Institution, student_id: uuid.UUID, semester: Semester):
    return UnitAssessment.objects.filter(student_id=student_id, semester=semester).select_related(
        "unit"
    )


def get_gpa_snapshot(
    institution: Institution, student_id: uuid.UUID, semester: Semester
) -> GPASnapshot | None:
    return GPASnapshot.objects.filter(student_id=student_id, semester=semester).first()


def get_dissertations(institution: Institution, student_id: uuid.UUID):
    return Dissertation.objects.filter(student_id=student_id)


def get_graduations(institution: Institution, student_id: uuid.UUID):
    return Graduation.objects.filter(student_id=student_id).select_related("programme")


def _resolve_grade_point(grading_scale, mean_pct: Decimal) -> Decimal | None:
    """`GradingScale.levels` gains an OPTIONAL `grade_point` key per level
    (e.g. `{"label": "A", "min": 80, "max": 100, "grade_point": 4.0}`) —
    backward-compatible, since `levels` is already a free-form JSONField
    and every other plugin only reads `label`/`min`/`max`."""
    if not grading_scale:
        return None
    for level in grading_scale.levels:
        if level["min"] <= mean_pct <= level["max"] and "grade_point" in level:
            return Decimal(str(level["grade_point"]))
    return None


def _compute_unit_grade_points(institution: Institution, assessments):
    """Groups `assessments` by unit, computes each unit's mean percentage,
    and resolves a grade point per unit. Returns a list of
    `(grade_point, credit_hours)` pairs, omitting units with no resolvable
    grade point (no assessments, or the grading scale doesn't cover that
    percentage)."""
    grading_scale = get_grading_scale(institution, InstitutionCurriculum.CurriculumType.UNIVERSITY)

    by_unit: dict[uuid.UUID, list] = {}
    for assessment in assessments:
        by_unit.setdefault(assessment.unit_id, []).append(assessment)

    results = []
    for unit_assessments in by_unit.values():
        unit = unit_assessments[0].unit
        percentages = [a.score / a.max_score * 100 for a in unit_assessments]
        mean_pct = sum(percentages) / len(percentages)
        grade_point = _resolve_grade_point(grading_scale, mean_pct)
        if grade_point is None:
            continue
        results.append((grade_point, unit.credit_hours))
    return results


def _weighted_gpa(grade_points: list) -> Decimal | None:
    if not grade_points:
        return None
    total_points = sum(gp * credit for gp, credit in grade_points)
    total_credits = sum(credit for _gp, credit in grade_points)
    return total_points / total_credits if total_credits else None


def compute_gpa(
    institution: Institution, student_id: uuid.UUID, semester: Semester
) -> Decimal | None:
    with bind_institution(institution):
        assessments = list(
            UnitAssessment.objects.filter(student_id=student_id, semester=semester).select_related(
                "unit"
            )
        )
        grade_points = _compute_unit_grade_points(institution, assessments)
    return _weighted_gpa(grade_points)


def compute_cgpa(institution: Institution, student_id: uuid.UUID) -> Decimal | None:
    """Cumulative across every `UnitAssessment` the student has ever had
    recorded, not scoped to one semester or ordered chronologically —
    `Semester` has no explicit ordering field, and inventing chronological-
    ordering logic the docs don't ask for would be scope creep."""
    with bind_institution(institution):
        assessments = list(
            UnitAssessment.objects.filter(student_id=student_id).select_related("unit")
        )
        grade_points = _compute_unit_grade_points(institution, assessments)
    return _weighted_gpa(grade_points)


def get_report_data(institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID) -> dict:
    student = get_student_by_id(student_id)
    semester = get_semester_for_term(institution, term_id)

    unit_assessments: list = []
    registrations: list = []
    gpa = cgpa = None
    if semester is not None:
        unit_assessments = list(get_unit_assessments(institution, student_id, semester))
        registrations = list(get_registrations(institution, student_id, semester))
        snapshot = get_gpa_snapshot(institution, student_id, semester)
        if snapshot is not None:
            gpa = str(snapshot.gpa)
            cgpa = str(snapshot.cgpa)

    dissertations = get_dissertations(institution, student_id)
    graduations = get_graduations(institution, student_id)

    return {
        "student_name": f"{student.first_name} {student.last_name}" if student else None,
        "unit_assessments": [
            {
                "unit": assessment.unit.name,
                "assessment_type": assessment.assessment_type,
                "score": str(assessment.score),
                "max_score": str(assessment.max_score),
            }
            for assessment in unit_assessments
        ],
        "registrations": [
            {"unit": registration.unit.name, "status": registration.status}
            for registration in registrations
        ],
        "gpa": gpa,
        "cgpa": cgpa,
        "dissertations": [
            {"title": dissertation.title, "status": dissertation.status}
            for dissertation in dissertations
        ],
        "graduations": [
            {
                "programme": graduation.programme.name,
                "conferred_at": graduation.conferred_at.isoformat(),
                "classification": graduation.classification,
            }
            for graduation in graduations
        ],
    }
