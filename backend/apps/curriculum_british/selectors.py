"""Public read interface for `curriculum_british` — docs/modules.md.

`compute_mean_coursework_grade` self-binds (explicit `institution`
argument, like `classes_streams.get_current_term`), same shape
`curriculum_844.selectors.compute_mean_and_grade` uses, kept consistent
even though nothing here runs from a Celery task yet.
"""

import uuid

from apps.academics.selectors import get_grading_scale
from apps.classes_streams.selectors import get_term
from apps.core.context import bind_institution
from apps.curriculum_british.models import Coursework, PredictedGrade
from apps.institutions.models import Institution, InstitutionCurriculum
from apps.students.selectors import get_student_by_id


def get_courseworks(institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID):
    return Coursework.objects.filter(student_id=student_id, term_id=term_id).select_related(
        "subject"
    )


def get_predicted_grades(
    institution: Institution, student_id: uuid.UUID, academic_year_id: uuid.UUID
):
    return PredictedGrade.objects.filter(
        student_id=student_id, academic_year_id=academic_year_id
    ).select_related("subject")


def compute_mean_coursework_grade(
    institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID
):
    """Unweighted mean of `(score/max_score*100)` across all `Coursework`
    for the term, resolved against `academics.GradingScale('british')`'s
    `levels`. Returns `(None, None)` when there's nothing to compute yet."""
    with bind_institution(institution):
        courseworks = list(Coursework.objects.filter(student_id=student_id, term_id=term_id))
        if not courseworks:
            return None, None

        percentages = [c.score / c.max_score * 100 for c in courseworks]
        mean_score = sum(percentages) / len(percentages)

        grading_scale = get_grading_scale(institution, InstitutionCurriculum.CurriculumType.BRITISH)
        mean_grade = ""
        if grading_scale:
            for level in grading_scale.levels:
                if level["min"] <= mean_score <= level["max"]:
                    mean_grade = level["label"]
                    break
    return mean_score, mean_grade


def get_report_data(institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID) -> dict:
    student = get_student_by_id(student_id)
    courseworks = get_courseworks(institution, student_id, term_id)
    mean_score, mean_grade = compute_mean_coursework_grade(institution, student_id, term_id)

    term = get_term(institution, term_id)
    predicted_grades = (
        get_predicted_grades(institution, student_id, term.academic_year_id) if term else []
    )

    return {
        "student_name": f"{student.first_name} {student.last_name}" if student else None,
        "courseworks": [
            {
                "subject": coursework.subject.name,
                "component": coursework.component,
                "score": str(coursework.score),
                "max_score": str(coursework.max_score),
            }
            for coursework in courseworks
        ],
        "mean_score": str(mean_score) if mean_score is not None else None,
        "mean_grade": mean_grade or None,
        "predicted_grades": [
            {"subject": grade.subject.name, "predicted_grade": grade.predicted_grade}
            for grade in predicted_grades
        ],
    }
