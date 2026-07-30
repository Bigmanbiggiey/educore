"""British's `AssessmentEngine`/`ReportEngine` implementation — thin
delegation to `services.py`/`selectors.py`, same shape as the other two
plugins' engines. No business logic lives here directly.
"""

from apps.academics.contracts import AssessmentEngine, ReportEngine
from apps.curriculum_british import selectors, services


class BritishEngine(AssessmentEngine, ReportEngine):
    def record_assessment(self, *, institution, student_id, term_id, details):
        coursework = services.record_coursework(
            institution=institution, student_id=student_id, term_id=term_id, details=details
        )
        return {
            "id": str(coursework.id),
            "subject_id": str(coursework.subject_id),
            "component": coursework.component,
            "score": str(coursework.score),
            "max_score": str(coursework.max_score),
        }

    def compute_result(self, *, institution, student_id, term_id):
        mean_score, mean_grade = selectors.compute_mean_coursework_grade(
            institution, student_id, term_id
        )
        if mean_score is None:
            return None
        return {"mean_score": str(mean_score), "mean_grade": mean_grade}

    def generate_report_data(self, *, institution, student_id, term_id):
        return selectors.get_report_data(institution, student_id, term_id)
