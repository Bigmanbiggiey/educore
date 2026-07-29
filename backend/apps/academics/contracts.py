"""The curriculum contract — docs/modules.md (`academics`). Every
`curriculum_*` app (Phase 3+) implements both of these; nothing in Layer
1/3 ever imports a `curriculum_*` app directly — only through
`selectors.get_curriculum_engine(institution, curriculum_type)`.

Signatures are concrete (not `*args, **kwargs`) as of Phase 3, now that a
real caller (`academics.views`' generic assessment/report-card endpoints,
docs/api-design.md §8) and a real implementation (`curriculum_cbc.CBCEngine`)
both exist — `student_id`/`term_id` stay plain UUIDs, not model instances,
matching the plain-cross-app-UUID convention every Layer 1 app already
follows. `details` carries curriculum-specific payload as a plain dict —
each engine validates/unpacks its own shape and raises `ValueError` on a
bad one, translated to a 400 by the calling view (same pattern as
`timetable.assign_slot`/`attendance.mark_attendance`).
"""

import uuid
from abc import ABC, abstractmethod
from typing import Any

from apps.institutions.models import Institution


class AssessmentEngine(ABC):
    @abstractmethod
    def record_assessment(
        self, *, institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID, details: dict
    ) -> Any:
        """Records a single assessment result for a student."""

    @abstractmethod
    def compute_result(
        self, *, institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID
    ) -> Any:
        """Computes a derived result (e.g. a term grade) from recorded
        assessments."""


class ReportEngine(ABC):
    @abstractmethod
    def generate_report_data(
        self, *, institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID
    ) -> Any:
        """Assembles the data a report card for `student_id` in `term_id`
        needs — curriculum-specific shape, curriculum-agnostic caller
        (`reports`, Phase 8)."""
