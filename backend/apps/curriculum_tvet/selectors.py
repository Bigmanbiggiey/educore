"""Public read interface for `curriculum_tvet` — docs/modules.md.

`compute_mean_practical_score` self-binds (explicit `institution` argument),
same shape `curriculum_844.selectors.compute_mean_and_grade`/
`curriculum_british.selectors.compute_mean_coursework_grade` use.
"""

import uuid

from apps.academics.selectors import get_grading_scale
from apps.core.context import bind_institution
from apps.curriculum_tvet.models import Certificate, IndustrialAttachment, PracticalAssessment
from apps.institutions.models import Institution, InstitutionCurriculum
from apps.students.selectors import get_student_by_id


def get_practical_assessments(institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID):
    return PracticalAssessment.objects.filter(
        student_id=student_id, term_id=term_id
    ).select_related("competency_unit")


def get_industrial_attachments(institution: Institution, student_id: uuid.UUID):
    return IndustrialAttachment.objects.filter(student_id=student_id)


def get_certificates(institution: Institution, student_id: uuid.UUID):
    return Certificate.objects.filter(student_id=student_id).select_related("course")


def compute_mean_practical_score(
    institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID
):
    """Unweighted mean of `(score/max_score*100)` across all
    `PracticalAssessment`s for the term, resolved against
    `academics.GradingScale('tvet')`'s `levels` — the generic label/min/max
    shape accommodates either a percentage-based or a Distinction/Credit/
    Pass/Fail competency-band convention, whichever an institution
    configures, without this plugin assuming one. Returns `(None, None)`
    when there's nothing to compute yet."""
    with bind_institution(institution):
        assessments = list(
            PracticalAssessment.objects.filter(student_id=student_id, term_id=term_id)
        )
        if not assessments:
            return None, None

        percentages = [a.score / a.max_score * 100 for a in assessments]
        mean_score = sum(percentages) / len(percentages)

        grading_scale = get_grading_scale(institution, InstitutionCurriculum.CurriculumType.TVET)
        mean_grade = ""
        if grading_scale:
            for level in grading_scale.levels:
                if level["min"] <= mean_score <= level["max"]:
                    mean_grade = level["label"]
                    break
    return mean_score, mean_grade


def get_report_data(institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID) -> dict:
    student = get_student_by_id(student_id)
    assessments = get_practical_assessments(institution, student_id, term_id)
    mean_score, mean_grade = compute_mean_practical_score(institution, student_id, term_id)
    attachments = get_industrial_attachments(institution, student_id)
    certificates = get_certificates(institution, student_id)

    return {
        "student_name": f"{student.first_name} {student.last_name}" if student else None,
        "practical_assessments": [
            {
                "competency_unit": assessment.competency_unit.name,
                "assessment_type": assessment.assessment_type,
                "score": str(assessment.score),
                "max_score": str(assessment.max_score),
            }
            for assessment in assessments
        ],
        "mean_score": str(mean_score) if mean_score is not None else None,
        "mean_grade": mean_grade or None,
        "industrial_attachments": [
            {
                "host_organization": attachment.host_organization,
                "start_date": str(attachment.start_date),
                "end_date": str(attachment.end_date),
            }
            for attachment in attachments
        ],
        "certificates": [
            {
                "course": certificate.course.name,
                "certificate_number": certificate.certificate_number,
                "issued_at": certificate.issued_at.isoformat(),
            }
            for certificate in certificates
        ],
    }
