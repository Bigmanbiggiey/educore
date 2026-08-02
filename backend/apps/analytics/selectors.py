"""Public read interface for `analytics` — docs/modules.md.

Every selector here takes `institution` explicitly and binds it via
`bind_institution`, same reasoning as every other Layer 1+ app's
selectors.py module docstring — `get_institution_summary` in particular is
consumed by `dashboard`'s Principal view, which has no ambient tenant of
its own beyond what it forwards from the request.
"""

import decimal
import uuid

from apps.analytics.models import AttendanceRateSnapshot, FeeCollectionSnapshot, MeanGradeRollup
from apps.classes_streams.models import ClassGrade
from apps.core.context import bind_institution
from apps.institutions.models import Institution


def get_attendance_rollup(
    institution: Institution, class_grade_id: uuid.UUID, term_id: uuid.UUID
) -> AttendanceRateSnapshot | None:
    with bind_institution(institution):
        return AttendanceRateSnapshot.objects.filter(
            class_grade_id=class_grade_id, term_id=term_id
        ).first()


def get_fee_collection_rollup(
    institution: Institution, class_grade_id: uuid.UUID, term_id: uuid.UUID
) -> FeeCollectionSnapshot | None:
    with bind_institution(institution):
        return FeeCollectionSnapshot.objects.filter(
            class_grade_id=class_grade_id, term_id=term_id
        ).first()


def get_mean_grade_rollup(
    institution: Institution, class_grade_id: uuid.UUID, term_id: uuid.UUID
) -> MeanGradeRollup | None:
    with bind_institution(institution):
        return MeanGradeRollup.objects.filter(
            class_grade_id=class_grade_id, term_id=term_id
        ).first()


def get_institution_summary(institution: Institution, term_id: uuid.UUID) -> dict:
    """Averages each rollup across every class in `term_id` — the
    institution-wide figures the Principal dashboard needs."""
    with bind_institution(institution):
        class_grade_ids = list(
            ClassGrade.objects.filter(term_id=term_id).values_list("id", flat=True)
        )
        attendance_rates = list(
            AttendanceRateSnapshot.objects.filter(
                class_grade_id__in=class_grade_ids, term_id=term_id, rate__isnull=False
            ).values_list("rate", flat=True)
        )
        collection_rates = list(
            FeeCollectionSnapshot.objects.filter(
                class_grade_id__in=class_grade_ids, term_id=term_id, collection_rate__isnull=False
            ).values_list("collection_rate", flat=True)
        )
    return {
        "class_count": len(class_grade_ids),
        "average_attendance_rate": _average(attendance_rates),
        "average_collection_rate": _average(collection_rates),
    }


def _average(values: list[decimal.Decimal]) -> decimal.Decimal | None:
    if not values:
        return None
    return sum(values) / len(values)
