"""Public write interface for `timetable` — docs/modules.md.

`assign_slot` is the one function worth calling out: it runs clash
detection before committing, because "the same staff member has two
overlapping periods" is a check across multiple `SubjectSlotAssignment`
rows (possibly on different `Timetable`s entirely), not something a single
row's own columns — or a `UniqueConstraint` on this table — can express.
"""

import datetime
import uuid

from django.db import transaction

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.timetable.models import Period, SubjectSlotAssignment, Timetable


def create_timetable(
    *, institution: Institution, term_id: uuid.UUID, class_grade_id: uuid.UUID
) -> Timetable:
    with bind_institution(institution):
        return Timetable.objects.create(
            institution_id=institution.id, term_id=term_id, class_grade_id=class_grade_id
        )


def create_period(
    *,
    institution: Institution,
    timetable: Timetable,
    day_of_week: int,
    start_time: datetime.time,
    end_time: datetime.time,
) -> Period:
    if start_time >= end_time:
        raise ValueError("start_time must be before end_time")
    with bind_institution(institution):
        return Period.objects.create(
            institution_id=institution.id,
            timetable=timetable,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
        )


@transaction.atomic
def assign_slot(
    *,
    institution: Institution,
    period: Period,
    subject_id: uuid.UUID,
    staff_id: uuid.UUID,
    room: str = "",
) -> SubjectSlotAssignment:
    with bind_institution(institution):
        clashes = (
            SubjectSlotAssignment.objects.filter(
                staff_id=staff_id,
                period__day_of_week=period.day_of_week,
                period__start_time__lt=period.end_time,
                period__end_time__gt=period.start_time,
            )
            .exclude(period=period)
            .exists()
        )
        if clashes:
            raise ValueError(
                f"Staff {staff_id} already has an overlapping period on "
                f"{period.get_day_of_week_display()} {period.start_time}-{period.end_time}."
            )
        assignment, _ = SubjectSlotAssignment.objects.update_or_create(
            period=period,
            defaults={
                "institution_id": institution.id,
                "subject_id": subject_id,
                "staff_id": staff_id,
                "room": room,
            },
        )
    return assignment
