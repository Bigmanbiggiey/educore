"""TVET's `AssessmentEngine`/`ReportEngine` implementation — thin
delegation to `services.py`/`selectors.py`, same shape as the other three
plugins' engines. No business logic lives here directly.
"""

from apps.academics.contracts import AssessmentEngine, ReportEngine
from apps.curriculum_tvet import selectors, services


class TVETEngine(AssessmentEngine, ReportEngine):
    def record_assessment(self, *, institution, student_id, term_id, details):
        assessment = services.record_practical_assessment(
            institution=institution, student_id=student_id, term_id=term_id, details=details
        )
        return {
            "id": str(assessment.id),
            "competency_unit_id": str(assessment.competency_unit_id),
            "assessment_type": assessment.assessment_type,
            "score": str(assessment.score),
            "max_score": str(assessment.max_score),
        }

    def compute_result(self, *, institution, student_id, term_id):
        mean_score, mean_grade = selectors.compute_mean_practical_score(
            institution, student_id, term_id
        )
        if mean_score is None:
            return None
        return {"mean_score": str(mean_score), "mean_grade": mean_grade}

    def generate_report_data(self, *, institution, student_id, term_id):
        return selectors.get_report_data(institution, student_id, term_id)
