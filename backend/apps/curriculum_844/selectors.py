"""Public read interface for `curriculum_844` — docs/modules.md.

`compute_mean_and_grade` self-binds (explicit `institution` argument, like
`classes_streams.get_current_term`) since it's called from
`services.recompute_mean_grade_snapshots`, which is documented to also run
from a Celery task with nothing ambiently bound.
"""

import uuid

from apps.academics.selectors import get_grading_scale
from apps.core.context import bind_institution
from apps.curriculum_844.models import ExamResult, MeanGradeSnapshot
from apps.institutions.models import Institution, InstitutionCurriculum
from apps.students.selectors import get_student_by_id


def get_exam_results(institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID):
    return ExamResult.objects.filter(student_id=student_id, term_id=term_id).select_related(
        "subject"
    )


def get_mean_grade_snapshot(
    institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID
) -> MeanGradeSnapshot | None:
    return MeanGradeSnapshot.objects.filter(student_id=student_id, term_id=term_id).first()


def compute_mean_and_grade(institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID):
    """Unweighted mean of `(score/max_score*100)` across every `ExamResult`
    for this student+term, regardless of `exam_type` — no documented
    weighting scheme exists between CAT/Midterm/EndTerm/Mock, so this
    doesn't invent one. Resolved against `academics.GradingScale('844')`'s
    `levels`. Returns `(None, None)` when there's nothing to compute yet."""
    with bind_institution(institution):
        results = list(ExamResult.objects.filter(student_id=student_id, term_id=term_id))
        if not results:
            return None, None

        percentages = [result.score / result.max_score * 100 for result in results]
        mean_score = sum(percentages) / len(percentages)

        grading_scale = get_grading_scale(
            institution, InstitutionCurriculum.CurriculumType.EIGHT_FOUR_FOUR
        )
        mean_grade = ""
        if grading_scale:
            for level in grading_scale.levels:
                if level["min"] <= mean_score <= level["max"]:
                    mean_grade = level["label"]
                    break
    return mean_score, mean_grade


def get_report_data(institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID) -> dict:
    student = get_student_by_id(student_id)
    results = get_exam_results(institution, student_id, term_id)
    snapshot = get_mean_grade_snapshot(institution, student_id, term_id)

    return {
        "student_name": f"{student.first_name} {student.last_name}" if student else None,
        "exam_results": [
            {
                "subject": result.subject.name,
                "exam_type": result.exam_type,
                "score": str(result.score),
                "max_score": str(result.max_score),
            }
            for result in results
        ],
        "mean_score": str(snapshot.mean_score) if snapshot else None,
        "mean_grade": snapshot.mean_grade if snapshot else None,
        "rank_in_class": snapshot.rank_in_class if snapshot else None,
        "rank_in_stream": snapshot.rank_in_stream if snapshot else None,
    }
