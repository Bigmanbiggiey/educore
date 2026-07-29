"""Public write interface for `attendance` — docs/modules.md.

`mark_attendance` is `update_or_create`-keyed on the unique constraint
(term, date, subject_type, target_id) — marking the same target on the
same day twice corrects the earlier record rather than duplicating it,
same idempotent-write pattern as `classes_streams.assign_class_teacher`
and `timetable.assign_slot`.
"""

import datetime
import uuid

from apps.attendance.models import AttendanceRecord
from apps.core.context import bind_institution
from apps.institutions.models import Institution


def mark_attendance(
    *,
    institution: Institution,
    term_id: uuid.UUID,
    date: datetime.date,
    subject_type: str,
    target_id: uuid.UUID,
    status: str,
) -> AttendanceRecord:
    if subject_type not in AttendanceRecord.SubjectType.values:
        raise ValueError(f"Unknown subject_type: {subject_type!r}")
    if status not in AttendanceRecord.Status.values:
        raise ValueError(f"Unknown status: {status!r}")
    with bind_institution(institution):
        record, _ = AttendanceRecord.objects.update_or_create(
            institution_id=institution.id,
            term_id=term_id,
            date=date,
            subject_type=subject_type,
            target_id=target_id,
            defaults={"status": status},
        )
    return record
