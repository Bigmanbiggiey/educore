"""University's `AssessmentEngine`/`ReportEngine` implementation — thin
delegation to `services.py`/`selectors.py`, same shape as the other four
plugins' engines. No business logic lives here directly.
"""

from apps.academics.contracts import AssessmentEngine, ReportEngine
from apps.curriculum_university import selectors, services


class UniversityEngine(AssessmentEngine, ReportEngine):
    def record_assessment(self, *, institution, student_id, term_id, details):
        assessment = services.record_unit_assessment(
            institution=institution, student_id=student_id, term_id=term_id, details=details
        )
        return {
            "id": str(assessment.id),
            "unit_id": str(assessment.unit_id),
            "assessment_type": assessment.assessment_type,
            "score": str(assessment.score),
            "max_score": str(assessment.max_score),
        }

    def compute_result(self, *, institution, student_id, term_id):
        semester = selectors.get_semester_for_term(institution, term_id)
        if semester is None:
            return None
        snapshot = selectors.get_gpa_snapshot(institution, student_id, semester)
        if snapshot is not None:
            return {"gpa": str(snapshot.gpa), "cgpa": str(snapshot.cgpa)}
        # No snapshot yet — a cheap, single-semester GPA-only calculation.
        # CGPA needs the student's full history and stays precompute-only
        # (docs/database.md §4).
        gpa = selectors.compute_gpa(institution, student_id, semester)
        if gpa is None:
            return None
        return {"gpa": str(gpa), "cgpa": None}

    def generate_report_data(self, *, institution, student_id, term_id):
        return selectors.get_report_data(institution, student_id, term_id)
