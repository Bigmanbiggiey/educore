"""Public read interface for `curriculum_cbc` — docs/modules.md."""

import uuid
from collections import Counter

from apps.curriculum_cbc.models import Competency, ContinuousAssessment, LearningArea, Project
from apps.institutions.models import Institution
from apps.students.selectors import get_student_by_id


def get_learning_areas(institution: Institution):
    return LearningArea.objects.all()


def get_competencies(institution: Institution, learning_area_id: uuid.UUID | None = None):
    queryset = Competency.objects.all()
    if learning_area_id is not None:
        queryset = queryset.filter(learning_area_id=learning_area_id)
    return queryset


def compute_term_result(institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID):
    """Per learning area, the mode (most common) performance level across
    this student's assessed competencies for the term — CBC has no single
    numeric grade, so "computes a derived result" (the ABC's own docstring)
    means this instead."""
    assessments = ContinuousAssessment.objects.filter(
        student_id=student_id, term_id=term_id
    ).select_related("competency__learning_area")

    levels_by_area: dict[uuid.UUID, list[str]] = {}
    names_by_area: dict[uuid.UUID, str] = {}
    for assessment in assessments:
        learning_area = assessment.competency.learning_area
        levels_by_area.setdefault(learning_area.id, []).append(assessment.performance_level)
        names_by_area[learning_area.id] = learning_area.name

    return [
        {
            "learning_area_id": str(learning_area_id),
            "learning_area_name": names_by_area[learning_area_id],
            "performance_level": Counter(levels).most_common(1)[0][0],
        }
        for learning_area_id, levels in levels_by_area.items()
    ]


def get_report_data(institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID) -> dict:
    student = get_student_by_id(student_id)
    assessments = ContinuousAssessment.objects.filter(
        student_id=student_id, term_id=term_id
    ).select_related("competency__learning_area")

    learning_areas: dict[uuid.UUID, dict] = {}
    for assessment in assessments:
        learning_area = assessment.competency.learning_area
        entry = learning_areas.setdefault(
            learning_area.id, {"learning_area": learning_area.name, "competencies": []}
        )
        entry["competencies"].append(
            {
                "strand": assessment.competency.strand,
                "sub_strand": assessment.competency.sub_strand,
                "performance_level": assessment.performance_level,
                "evidence_notes": assessment.evidence_notes,
            }
        )

    projects = Project.objects.filter(student_id=student_id, term_id=term_id).select_related(
        "competency"
    )

    return {
        "student_name": f"{student.first_name} {student.last_name}" if student else None,
        "learning_areas": list(learning_areas.values()),
        "projects": [
            {"competency": project.competency.strand, "description": project.description}
            for project in projects
        ],
    }
