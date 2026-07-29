"""Public read interface for `attendance` — docs/modules.md.

Every selector here takes `institution` explicitly and binds it via
`bind_institution`, same reasoning as every other Layer 1 app's
selectors.py module docstring.
"""

import datetime
import uuid

from apps.attendance.models import AttendanceRecord
from apps.core.context import bind_institution
from apps.institutions.models import Institution

# Statuses that count as "attended" for rate purposes — a student/staff
# member marked late was still physically present, unlike absent/excused.
_ATTENDED_STATUSES = (AttendanceRecord.Status.PRESENT, AttendanceRecord.Status.LATE)


def get_records(
    institution: Institution,
    subject_type: str,
    target_id: uuid.UUID,
    term_id: uuid.UUID | None = None,
):
    with bind_institution(institution):
        qs = AttendanceRecord.objects.filter(subject_type=subject_type, target_id=target_id)
        if term_id is not None:
            qs = qs.filter(term_id=term_id)
        return list(qs)


def get_attendance_rate(
    institution: Institution,
    subject_type: str,
    target_id: uuid.UUID,
    term_id: uuid.UUID | None = None,
) -> float | None:
    """Fraction of records marked present or late, out of all records for
    this target — `None` (not `0.0`) when there are no records at all, so
    callers can distinguish "perfect attendance" from "no data yet"."""
    with bind_institution(institution):
        qs = AttendanceRecord.objects.filter(subject_type=subject_type, target_id=target_id)
        if term_id is not None:
            qs = qs.filter(term_id=term_id)
        total = qs.count()
        if total == 0:
            return None
        attended = qs.filter(status__in=_ATTENDED_STATUSES).count()
        return attended / total


def get_records_for_date(institution: Institution, subject_type: str, date: datetime.date):
    with bind_institution(institution):
        return list(AttendanceRecord.objects.filter(subject_type=subject_type, date=date))
