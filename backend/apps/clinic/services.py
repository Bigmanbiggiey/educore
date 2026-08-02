"""Public write interface for `clinic` — docs/modules.md.

`set_health_record` is `update_or_create`-keyed on `student_id` — a student
has at most one `HealthRecord` (`healthrecord_one_per_student`), so
recording an update corrects the row in place rather than duplicating it,
same idempotent-write pattern `attendance.mark_attendance` established.
`record_visit`/`add_medication` are plain wrappers — neither has an
invariant beyond its own columns.
"""

import datetime
import uuid

from apps.clinic.models import ClinicVisit, HealthRecord, Medication
from apps.core.context import bind_institution
from apps.institutions.models import Institution


def set_health_record(
    *,
    institution: Institution,
    student_id: uuid.UUID,
    allergies: str = "",
    conditions: str = "",
    blood_group: str = "",
) -> HealthRecord:
    with bind_institution(institution):
        record, _ = HealthRecord.objects.update_or_create(
            institution_id=institution.id,
            student_id=student_id,
            defaults={
                "allergies": allergies,
                "conditions": conditions,
                "blood_group": blood_group,
            },
        )
    return record


def record_visit(
    *,
    institution: Institution,
    student_id: uuid.UUID,
    visit_date: datetime.date,
    treated_by_id: uuid.UUID,
    notes: str = "",
) -> ClinicVisit:
    with bind_institution(institution):
        return ClinicVisit.objects.create(
            institution_id=institution.id,
            student_id=student_id,
            visit_date=visit_date,
            treated_by_id=treated_by_id,
            notes=notes,
        )


def add_medication(
    *, institution: Institution, visit: ClinicVisit, name: str, dosage: str = "", notes: str = ""
) -> Medication:
    with bind_institution(institution):
        return Medication.objects.create(
            institution_id=institution.id, visit=visit, name=name, dosage=dosage, notes=notes
        )
