"""Public write interface for `curriculum_tvet` — docs/modules.md.

`record_practical_assessment` is the function `TVETEngine.record_assessment`
delegates to, same role as the other three plugins' assessment-recording
functions.
"""

import datetime
import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from apps.core.context import bind_institution
from apps.curriculum_tvet.models import (
    Certificate,
    CompetencyUnit,
    Course,
    IndustrialAttachment,
    PracticalAssessment,
    TVETDepartment,
)
from apps.institutions.models import Institution


def create_department(*, institution: Institution, name: str) -> TVETDepartment:
    with bind_institution(institution):
        return TVETDepartment.objects.create(institution_id=institution.id, name=name)


def create_course(
    *, institution: Institution, department: TVETDepartment, course_code: str, name: str
) -> Course:
    with bind_institution(institution):
        return Course.objects.create(
            institution_id=institution.id, department=department, course_code=course_code, name=name
        )


def create_competency_unit(
    *, institution: Institution, course: Course, unit_code: str, name: str, credit_hours: int
) -> CompetencyUnit:
    with bind_institution(institution):
        return CompetencyUnit.objects.create(
            institution_id=institution.id,
            course=course,
            unit_code=unit_code,
            name=name,
            credit_hours=credit_hours,
        )


def create_industrial_attachment(
    *,
    institution: Institution,
    student_id: uuid.UUID,
    host_organization: str,
    start_date: datetime.date,
    end_date: datetime.date,
    supervisor_report: str = "",
) -> IndustrialAttachment:
    if start_date >= end_date:
        raise ValueError("start_date must be before end_date")
    with bind_institution(institution):
        return IndustrialAttachment.objects.create(
            institution_id=institution.id,
            student_id=student_id,
            host_organization=host_organization,
            start_date=start_date,
            end_date=end_date,
            supervisor_report=supervisor_report,
        )


def issue_certificate(
    *,
    institution: Institution,
    student_id: uuid.UUID,
    course: Course,
    certificate_number: str,
    issued_at: datetime.datetime | None = None,
) -> Certificate:
    with bind_institution(institution):
        return Certificate.objects.create(
            institution_id=institution.id,
            student_id=student_id,
            course=course,
            certificate_number=certificate_number,
            issued_at=issued_at or timezone.now(),
        )


def record_practical_assessment(
    *, institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID, details: dict
) -> PracticalAssessment:
    try:
        competency_unit_id = details["competency_unit_id"]
        assessment_type = details["assessment_type"]
        raw_score = details["score"]
        raw_max_score = details["max_score"]
        assessor_id = details["assessor_id"]
    except KeyError as exc:
        raise ValueError(f"TVET practical assessment details missing required key: {exc}") from None

    if assessment_type not in PracticalAssessment.AssessmentType.values:
        raise ValueError(f"Unknown assessment_type: {assessment_type!r}")

    try:
        score = Decimal(str(raw_score))
        max_score = Decimal(str(raw_max_score))
    except Exception as exc:
        raise ValueError("score/max_score must be numeric.") from exc
    if max_score <= 0 or score < 0 or score > max_score:
        raise ValueError("score must be between 0 and max_score, and max_score must be positive.")

    with bind_institution(institution):
        try:
            competency_unit = CompetencyUnit.objects.get(id=competency_unit_id)
        except (CompetencyUnit.DoesNotExist, DjangoValidationError):
            raise ValueError(f"No competency unit matches id {competency_unit_id!r}.") from None

        assessment, _ = PracticalAssessment.objects.update_or_create(
            institution_id=institution.id,
            student_id=student_id,
            competency_unit=competency_unit,
            term_id=term_id,
            assessment_type=assessment_type,
            defaults={"score": score, "max_score": max_score, "assessor_id": assessor_id},
        )
    return assessment
