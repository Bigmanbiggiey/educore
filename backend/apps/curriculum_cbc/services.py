"""Public write interface for `curriculum_cbc` — docs/modules.md.

`record_assessment` is the function `CBCEngine.record_assessment` (and, one
layer up, `academics.views.AssessmentRecordView`) delegates to. `details`
arrives as a plain dict from the curriculum-agnostic caller (docs/api-design.md
§8) — this function owns validating its own shape and raises `ValueError`
on anything wrong, translated to a 400 by the view that eventually calls it.
"""

import uuid

from django.core.exceptions import ValidationError as DjangoValidationError

from apps.core.context import bind_institution
from apps.curriculum_cbc.models import (
    PCI,
    Competency,
    ContinuousAssessment,
    CoreValue,
    LearningArea,
    Project,
)
from apps.institutions.models import Institution


def create_learning_area(
    *, institution: Institution, subject_catalog_id: uuid.UUID, name: str, code: str
) -> LearningArea:
    with bind_institution(institution):
        return LearningArea.objects.create(
            institution_id=institution.id,
            subject_catalog_id=subject_catalog_id,
            name=name,
            code=code,
        )


def create_competency(
    *, institution: Institution, learning_area: LearningArea, strand: str, sub_strand: str = ""
) -> Competency:
    with bind_institution(institution):
        return Competency.objects.create(
            institution_id=institution.id,
            learning_area=learning_area,
            strand=strand,
            sub_strand=sub_strand,
        )


def create_core_value(*, institution: Institution, name: str, description: str = "") -> CoreValue:
    with bind_institution(institution):
        return CoreValue.objects.create(
            institution_id=institution.id, name=name, description=description
        )


def create_pci(*, institution: Institution, name: str, description: str = "") -> PCI:
    with bind_institution(institution):
        return PCI.objects.create(institution_id=institution.id, name=name, description=description)


def create_project(
    *,
    institution: Institution,
    student_id: uuid.UUID,
    competency: Competency,
    term_id: uuid.UUID,
    description: str = "",
) -> Project:
    with bind_institution(institution):
        return Project.objects.create(
            institution_id=institution.id,
            student_id=student_id,
            competency=competency,
            term_id=term_id,
            description=description,
        )


def record_assessment(
    *, institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID, details: dict
) -> ContinuousAssessment:
    try:
        competency_id = details["competency_id"]
        performance_level = details["performance_level"]
    except KeyError as exc:
        raise ValueError(f"CBC assessment details missing required key: {exc}") from None
    evidence_notes = details.get("evidence_notes", "")

    if performance_level not in ContinuousAssessment.PerformanceLevel.values:
        raise ValueError(f"Unknown performance_level: {performance_level!r}")

    with bind_institution(institution):
        try:
            competency = Competency.objects.get(id=competency_id)
        except (Competency.DoesNotExist, DjangoValidationError):
            raise ValueError(f"No competency matches id {competency_id!r}.") from None

        assessment, _ = ContinuousAssessment.objects.update_or_create(
            institution_id=institution.id,
            student_id=student_id,
            competency=competency,
            term_id=term_id,
            defaults={"performance_level": performance_level, "evidence_notes": evidence_notes},
        )
    return assessment
