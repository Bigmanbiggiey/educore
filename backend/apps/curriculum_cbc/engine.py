"""CBC's `AssessmentEngine`/`ReportEngine` implementation — thin delegation
to `services.py`/`selectors.py`, exactly like every other app's
function-based services/selectors split. No business logic lives here
directly; this class exists only to satisfy the registry/ABC contract
(`apps/academics/registry.py`).
"""

from apps.academics.contracts import AssessmentEngine, ReportEngine
from apps.curriculum_cbc import selectors, services


class CBCEngine(AssessmentEngine, ReportEngine):
    def record_assessment(self, *, institution, student_id, term_id, details):
        assessment = services.record_assessment(
            institution=institution, student_id=student_id, term_id=term_id, details=details
        )
        return {
            "id": str(assessment.id),
            "competency_id": str(assessment.competency_id),
            "performance_level": assessment.performance_level,
        }

    def compute_result(self, *, institution, student_id, term_id):
        return selectors.compute_term_result(institution, student_id, term_id)

    def generate_report_data(self, *, institution, student_id, term_id):
        return selectors.get_report_data(institution, student_id, term_id)
