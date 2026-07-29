"""Public read interface for `timetable` — docs/modules.md.

Every selector here takes `institution` explicitly and binds it via
`bind_institution` (see `classes_streams.selectors`'s module docstring for
why), so these work correctly both inside a request and from a context
with nothing bound at all.
"""

import uuid

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.timetable.models import Period, SubjectSlotAssignment, Timetable


def get_timetable(
    institution: Institution, class_grade_id: uuid.UUID, term_id: uuid.UUID
) -> Timetable | None:
    with bind_institution(institution):
        return Timetable.objects.filter(class_grade_id=class_grade_id, term_id=term_id).first()


def get_periods(institution: Institution, timetable_id: uuid.UUID):
    with bind_institution(institution):
        return list(Period.objects.filter(timetable_id=timetable_id))


def get_staff_schedule(institution: Institution, staff_id: uuid.UUID):
    """Every `SubjectSlotAssignment` for one staff member across every
    timetable at the institution — the same shape `services.assign_slot`'s
    clash-detection query uses, exposed here so other apps (`staff`'s own
    "assigned classes" selector, once built) don't need to duplicate it."""
    with bind_institution(institution):
        return list(
            SubjectSlotAssignment.objects.filter(staff_id=staff_id).select_related(
                "period", "period__timetable"
            )
        )
