"""Public write interface for `analytics` — docs/modules.md:
Celery-driven rollups, precomputed rather than calculated per request.
`analytics` never writes to any other app's tables (docs/modules.md's own
dependency note) — only its own three snapshot models, via the selectors
every other Layer 1/2 app already exposes for exactly this kind of
cross-app read.

`compute_rollups` is the one function this app needs — each of the three
metrics is `update_or_create`-keyed on `(institution, class_grade, term)`,
same idempotent-recompute shape `curriculum_844.services.
recompute_mean_grade_snapshots` established.
"""

import decimal
import uuid

from apps.analytics.models import AttendanceRateSnapshot, FeeCollectionSnapshot, MeanGradeRollup
from apps.attendance.models import AttendanceRecord
from apps.attendance.selectors import get_attendance_rate
from apps.classes_streams.models import ClassGrade
from apps.core.context import bind_institution
from apps.curriculum_844.selectors import get_mean_grade_snapshot
from apps.finance.selectors import get_balance, get_invoices_for_student
from apps.institutions.models import Institution, InstitutionCurriculum
from apps.students.selectors import get_active_roster


def compute_rollups(
    *, institution: Institution, class_grade: ClassGrade, term_id: uuid.UUID
) -> dict:
    with bind_institution(institution):
        roster = list(get_active_roster(class_grade.id))

        attendance_rate = _average_attendance_rate(institution, roster, term_id)
        total_due, total_collected, collection_rate = _fee_collection(institution, roster, term_id)
        mean_score, mean_grade = _mean_grade(institution, class_grade, roster, term_id)

        attendance_snapshot, _ = AttendanceRateSnapshot.objects.update_or_create(
            institution_id=institution.id,
            class_grade_id=class_grade.id,
            term_id=term_id,
            defaults={"rate": attendance_rate},
        )
        fee_snapshot, _ = FeeCollectionSnapshot.objects.update_or_create(
            institution_id=institution.id,
            class_grade_id=class_grade.id,
            term_id=term_id,
            defaults={
                "total_due": total_due,
                "total_collected": total_collected,
                "collection_rate": collection_rate,
            },
        )
        grade_rollup, _ = MeanGradeRollup.objects.update_or_create(
            institution_id=institution.id,
            class_grade_id=class_grade.id,
            term_id=term_id,
            defaults={"mean_score": mean_score, "mean_grade": mean_grade},
        )
    return {
        "attendance": attendance_snapshot,
        "fee_collection": fee_snapshot,
        "mean_grade": grade_rollup,
    }


def _average_attendance_rate(institution, roster, term_id) -> decimal.Decimal | None:
    rates = []
    for student in roster:
        rate = get_attendance_rate(
            institution, AttendanceRecord.SubjectType.STUDENT, student.id, term_id
        )
        if rate is not None:
            rates.append(decimal.Decimal(str(rate)))
    if not rates:
        return None
    return sum(rates) / len(rates)


def _fee_collection(
    institution, roster, term_id
) -> tuple[decimal.Decimal, decimal.Decimal, decimal.Decimal | None]:
    total_due = decimal.Decimal("0")
    total_collected = decimal.Decimal("0")
    for student in roster:
        invoices = get_invoices_for_student(institution, student.id, term_id)
        due = sum((invoice.amount_due for invoice in invoices), decimal.Decimal("0"))
        balance = get_balance(institution, student.id, term_id)
        total_due += due
        total_collected += due - balance
    collection_rate = (total_collected / total_due) if total_due > 0 else None
    return total_due, total_collected, collection_rate


def _mean_grade(institution, class_grade, roster, term_id) -> tuple[decimal.Decimal | None, str]:
    if class_grade.curriculum_type != InstitutionCurriculum.CurriculumType.EIGHT_FOUR_FOUR:
        return None, ""
    scores = []
    grades = []
    for student in roster:
        snapshot = get_mean_grade_snapshot(institution, student.id, term_id)
        if snapshot is not None:
            scores.append(snapshot.mean_score)
            grades.append(snapshot.mean_grade)
    if not scores:
        return None, ""
    mean_score = sum(scores) / len(scores)
    # Individual letter grades have no well-defined mean, so the class's
    # summary letter grade is the grade of whichever student's own mean
    # score sits closest to the class mean score — a simple, defensible
    # stand-in, not a real statistical average.
    mean_grade = min(zip(scores, grades, strict=False), key=lambda pair: abs(pair[0] - mean_score))[
        1
    ]
    return mean_score, mean_grade
