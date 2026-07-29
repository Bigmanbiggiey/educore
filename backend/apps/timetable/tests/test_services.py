import uuid

from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.timetable.models import SubjectSlotAssignment
from apps.timetable.services import assign_slot, create_period, create_timetable


class TimetableServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def _timetable(self):
        return create_timetable(
            institution=self.institution, term_id=uuid.uuid4(), class_grade_id=uuid.uuid4()
        )

    def _period(self, timetable=None, day_of_week=0, start_time="08:00", end_time="09:00"):
        return create_period(
            institution=self.institution,
            timetable=timetable or self._timetable(),
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
        )


class CreatePeriodTests(TimetableServiceTestCase):
    def test_rejects_a_start_time_after_the_end_time(self):
        with self.assertRaises(ValueError):
            self._period(start_time="09:00", end_time="08:00")


class AssignSlotTests(TimetableServiceTestCase):
    def test_creates_a_new_assignment(self):
        period = self._period()
        staff_id = uuid.uuid4()

        assignment = assign_slot(
            institution=self.institution, period=period, subject_id=uuid.uuid4(), staff_id=staff_id
        )

        self.assertEqual(assignment.staff_id, staff_id)
        with bind_institution(self.institution):
            self.assertEqual(SubjectSlotAssignment.objects.count(), 1)

    def test_reassigning_the_same_period_updates_rather_than_duplicates(self):
        period = self._period()
        first_staff = uuid.uuid4()
        second_staff = uuid.uuid4()

        assign_slot(
            institution=self.institution,
            period=period,
            subject_id=uuid.uuid4(),
            staff_id=first_staff,
        )
        assign_slot(
            institution=self.institution,
            period=period,
            subject_id=uuid.uuid4(),
            staff_id=second_staff,
        )

        with bind_institution(self.institution):
            self.assertEqual(SubjectSlotAssignment.objects.count(), 1)
            self.assertEqual(SubjectSlotAssignment.objects.first().staff_id, second_staff)

    def test_rejects_an_overlapping_assignment_for_the_same_staff_on_a_different_timetable(self):
        staff_id = uuid.uuid4()
        first_period = self._period(day_of_week=0, start_time="08:00", end_time="09:00")
        # A different Timetable (different class_grade) — the clash still
        # has to be caught, since it's the same staff member double-booked
        # on the same day/time, regardless of which class each period
        # belongs to.
        second_period = self._period(day_of_week=0, start_time="08:30", end_time="09:30")

        assign_slot(
            institution=self.institution,
            period=first_period,
            subject_id=uuid.uuid4(),
            staff_id=staff_id,
        )

        with self.assertRaises(ValueError):
            assign_slot(
                institution=self.institution,
                period=second_period,
                subject_id=uuid.uuid4(),
                staff_id=staff_id,
            )

    def test_allows_non_overlapping_periods_for_the_same_staff_on_the_same_day(self):
        staff_id = uuid.uuid4()
        first_period = self._period(day_of_week=0, start_time="08:00", end_time="09:00")
        second_period = self._period(day_of_week=0, start_time="09:00", end_time="10:00")

        assign_slot(
            institution=self.institution,
            period=first_period,
            subject_id=uuid.uuid4(),
            staff_id=staff_id,
        )
        assign_slot(
            institution=self.institution,
            period=second_period,
            subject_id=uuid.uuid4(),
            staff_id=staff_id,
        )  # must not raise

    def test_allows_the_same_staff_at_the_same_time_on_a_different_day(self):
        staff_id = uuid.uuid4()
        first_period = self._period(day_of_week=0, start_time="08:00", end_time="09:00")
        second_period = self._period(day_of_week=1, start_time="08:00", end_time="09:00")

        assign_slot(
            institution=self.institution,
            period=first_period,
            subject_id=uuid.uuid4(),
            staff_id=staff_id,
        )
        assign_slot(
            institution=self.institution,
            period=second_period,
            subject_id=uuid.uuid4(),
            staff_id=staff_id,
        )  # must not raise

    def test_a_different_staff_member_can_take_an_overlapping_period(self):
        first_period = self._period(day_of_week=0, start_time="08:00", end_time="09:00")
        second_period = self._period(day_of_week=0, start_time="08:30", end_time="09:30")

        assign_slot(
            institution=self.institution,
            period=first_period,
            subject_id=uuid.uuid4(),
            staff_id=uuid.uuid4(),
        )
        assign_slot(
            institution=self.institution,
            period=second_period,
            subject_id=uuid.uuid4(),
            staff_id=uuid.uuid4(),
        )  # must not raise
