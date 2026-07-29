"""Public write interface for `curriculum_844` — docs/modules.md.

`record_exam_result` is the function `EightFourFourEngine.record_assessment`
delegates to, same role as `curriculum_cbc.services.record_assessment`.
`recompute_mean_grade_snapshots` is the real logic behind `tasks.py`'s
Celery task — ranking needs every active student in the class recomputed
together, so it's only ever run administratively (docs/database.md §4:
"after results entry closes"), never live per request.
"""

import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from apps.core.context import bind_institution
from apps.curriculum_844.models import ExamResult, MeanGradeSnapshot, Subject
from apps.curriculum_844.selectors import compute_mean_and_grade
from apps.institutions.models import Institution
from apps.students.selectors import get_active_enrollments


def create_subject(
    *, institution: Institution, subject_catalog_id: uuid.UUID, name: str, code: str
) -> Subject:
    with bind_institution(institution):
        return Subject.objects.create(
            institution_id=institution.id,
            subject_catalog_id=subject_catalog_id,
            name=name,
            code=code,
        )


def record_exam_result(
    *, institution: Institution, student_id: uuid.UUID, term_id: uuid.UUID, details: dict
) -> ExamResult:
    try:
        subject_id = details["subject_id"]
        exam_type = details["exam_type"]
        raw_score = details["score"]
        raw_max_score = details["max_score"]
    except KeyError as exc:
        raise ValueError(f"8-4-4 exam result details missing required key: {exc}") from None

    if exam_type not in ExamResult.ExamType.values:
        raise ValueError(f"Unknown exam_type: {exam_type!r}")

    try:
        score = Decimal(str(raw_score))
        max_score = Decimal(str(raw_max_score))
    except Exception as exc:
        raise ValueError("score/max_score must be numeric.") from exc
    if max_score <= 0 or score < 0 or score > max_score:
        raise ValueError("score must be between 0 and max_score, and max_score must be positive.")

    with bind_institution(institution):
        try:
            subject = Subject.objects.get(id=subject_id)
        except (Subject.DoesNotExist, DjangoValidationError):
            raise ValueError(f"No subject matches id {subject_id!r}.") from None

        result, _ = ExamResult.objects.update_or_create(
            institution_id=institution.id,
            student_id=student_id,
            subject=subject,
            term_id=term_id,
            exam_type=exam_type,
            defaults={"score": score, "max_score": max_score},
        )
    return result


@transaction.atomic
def import_kcpe_kcse_results(
    *, institution: Institution, term_id: uuid.UUID, rows: list[dict]
) -> list[ExamResult]:
    results = []
    for row in rows:
        details = {
            "subject_id": row["subject_id"],
            "exam_type": ExamResult.ExamType.KCPE_KCSE,
            "score": row["score"],
            "max_score": row["max_score"],
        }
        results.append(
            record_exam_result(
                institution=institution,
                student_id=row["student_id"],
                term_id=term_id,
                details=details,
            )
        )
    return results


def recompute_mean_grade_snapshots(
    *, institution: Institution, term_id: uuid.UUID, class_grade_id: uuid.UUID
) -> list[MeanGradeSnapshot]:
    enrollments = get_active_enrollments(institution, class_grade_id, term_id)

    per_student = []
    for enrollment in enrollments:
        mean_score, mean_grade = compute_mean_and_grade(institution, enrollment.student_id, term_id)
        if mean_score is None:
            continue
        per_student.append((enrollment.student_id, enrollment.stream_id, mean_score, mean_grade))

    ranked_by_class = sorted(per_student, key=lambda row: row[2], reverse=True)
    class_ranks = {
        student_id: rank for rank, (student_id, _, _, _) in enumerate(ranked_by_class, start=1)
    }

    by_stream: dict[uuid.UUID | None, list] = {}
    for row in per_student:
        by_stream.setdefault(row[1], []).append(row)
    stream_ranks: dict[uuid.UUID, int] = {}
    for rows in by_stream.values():
        ranked = sorted(rows, key=lambda row: row[2], reverse=True)
        for rank, (student_id, _, _, _) in enumerate(ranked, start=1):
            stream_ranks[student_id] = rank

    snapshots = []
    with bind_institution(institution):
        for student_id, _stream_id, mean_score, mean_grade in per_student:
            snapshot, _ = MeanGradeSnapshot.objects.update_or_create(
                institution_id=institution.id,
                student_id=student_id,
                term_id=term_id,
                defaults={
                    "mean_score": mean_score,
                    "mean_grade": mean_grade,
                    "rank_in_class": class_ranks[student_id],
                    "rank_in_stream": stream_ranks.get(student_id),
                },
            )
            snapshots.append(snapshot)
    return snapshots
