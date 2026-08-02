"""Public read interface for `clinic` — docs/modules.md. Every selector
here takes `institution` explicitly and binds it via `bind_institution`,
same reasoning as every other Layer 1 app's selectors.py module docstring.

The nurse-role restriction docs/modules.md calls out for this app's
selectors is enforced by the caller (`views.py`'s permission classes,
docs/permissions.md §6), not here — see `models.py`'s module docstring.
"""

import uuid

from apps.clinic.models import ClinicVisit, HealthRecord, Medication
from apps.core.context import bind_institution
from apps.institutions.models import Institution


def get_health_record(institution: Institution, student_id: uuid.UUID) -> HealthRecord | None:
    with bind_institution(institution):
        return HealthRecord.objects.filter(student_id=student_id).first()


def get_visits(institution: Institution, student_id: uuid.UUID):
    with bind_institution(institution):
        return list(ClinicVisit.objects.filter(student_id=student_id))


def get_medications(institution: Institution, visit_id: uuid.UUID):
    with bind_institution(institution):
        return list(Medication.objects.filter(visit_id=visit_id))
