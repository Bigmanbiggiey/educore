"""The curriculum contract — docs/modules.md (`academics`). Abstract only,
no implementation: this is the mechanism behind "future curricula must be
addable without rewriting existing code." Every `curriculum_*` app (Phase 3)
implements both of these; nothing in Layer 1/3 ever imports a `curriculum_*`
app directly — only through `selectors.get_curriculum_engine(institution)`.
"""

from abc import ABC, abstractmethod
from typing import Any


class AssessmentEngine(ABC):
    @abstractmethod
    def record_assessment(self, *args: Any, **kwargs: Any) -> Any:
        """Records a single assessment result for a student."""

    @abstractmethod
    def compute_result(self, *args: Any, **kwargs: Any) -> Any:
        """Computes a derived result (e.g. a term grade) from recorded
        assessments."""


class ReportEngine(ABC):
    @abstractmethod
    def generate_report_data(self, student: Any, term: Any) -> Any:
        """Assembles the data a report card for `student` in `term` needs —
        curriculum-specific shape, curriculum-agnostic caller (`reports`,
        Phase 8)."""
