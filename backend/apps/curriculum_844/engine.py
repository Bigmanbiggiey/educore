"""8-4-4's `AssessmentEngine`/`ReportEngine` implementation — thin
delegation to `services.py`/`selectors.py`, same shape as
`curriculum_cbc.CBCEngine`. No business logic lives here directly.
"""

from apps.academics.contracts import AssessmentEngine, ReportEngine
from apps.curriculum_844 import selectors, services


class EightFourFourEngine(AssessmentEngine, ReportEngine):
    def record_assessment(self, *, institution, student_id, term_id, details):
        result = services.record_exam_result(
            institution=institution, student_id=student_id, term_id=term_id, details=details
        )
        return {
            "id": str(result.id),
            "subject_id": str(result.subject_id),
            "exam_type": result.exam_type,
            "score": str(result.score),
            "max_score": str(result.max_score),
        }

    def compute_result(self, *, institution, student_id, term_id):
        snapshot = selectors.get_mean_grade_snapshot(institution, student_id, term_id)
        if snapshot is not None:
            return {
                "mean_score": str(snapshot.mean_score),
                "mean_grade": snapshot.mean_grade,
                "rank_in_class": snapshot.rank_in_class,
                "rank_in_stream": snapshot.rank_in_stream,
            }
        # No snapshot yet — a cheap, single-student, unranked calculation.
        # Ranking needs every student in the class recomputed together and
        # stays precompute-only (docs/database.md §4).
        mean_score, mean_grade = selectors.compute_mean_and_grade(institution, student_id, term_id)
        if mean_score is None:
            return None
        return {
            "mean_score": str(mean_score),
            "mean_grade": mean_grade,
            "rank_in_class": None,
            "rank_in_stream": None,
        }

    def generate_report_data(self, *, institution, student_id, term_id):
        return selectors.get_report_data(institution, student_id, term_id)
