import uuid

from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.timetable.models import Period, SubjectSlotAssignment, Timetable
from apps.timetable.selectors import get_periods, get_staff_schedule, get_timetable


class TimetableSelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)


class GetTimetableTests(TimetableSelectorTestCase):
    def test_returns_the_matching_timetable(self):
        term_id = uuid.uuid4()
        class_grade_id = uuid.uuid4()
        timetable = Timetable.objects.create(
            institution_id=self.institution.id, term_id=term_id, class_grade_id=class_grade_id
        )
        self.assertEqual(get_timetable(self.institution, class_grade_id, term_id), timetable)

    def test_returns_none_when_no_timetable_exists(self):
        self.assertIsNone(get_timetable(self.institution, uuid.uuid4(), uuid.uuid4()))


class GetPeriodsTests(TimetableSelectorTestCase):
    def test_returns_periods_for_the_timetable(self):
        timetable = Timetable.objects.create(
            institution_id=self.institution.id, term_id=uuid.uuid4(), class_grade_id=uuid.uuid4()
        )
        other_timetable = Timetable.objects.create(
            institution_id=self.institution.id, term_id=uuid.uuid4(), class_grade_id=uuid.uuid4()
        )
        period = Period.objects.create(
            institution_id=self.institution.id,
            timetable=timetable,
            day_of_week=0,
            start_time="08:00",
            end_time="09:00",
        )
        Period.objects.create(
            institution_id=self.institution.id,
            timetable=other_timetable,
            day_of_week=0,
            start_time="08:00",
            end_time="09:00",
        )

        self.assertEqual(get_periods(self.institution, timetable.id), [period])


class GetStaffScheduleTests(TimetableSelectorTestCase):
    def test_returns_assignments_for_the_staff_member(self):
        timetable = Timetable.objects.create(
            institution_id=self.institution.id, term_id=uuid.uuid4(), class_grade_id=uuid.uuid4()
        )
        period = Period.objects.create(
            institution_id=self.institution.id,
            timetable=timetable,
            day_of_week=0,
            start_time="08:00",
            end_time="09:00",
        )
        staff_id = uuid.uuid4()
        assignment = SubjectSlotAssignment.objects.create(
            institution_id=self.institution.id,
            period=period,
            subject_id=uuid.uuid4(),
            staff_id=staff_id,
        )
        SubjectSlotAssignment.objects.create(
            institution_id=self.institution.id,
            period=Period.objects.create(
                institution_id=self.institution.id,
                timetable=timetable,
                day_of_week=1,
                start_time="08:00",
                end_time="09:00",
            ),
            subject_id=uuid.uuid4(),
            staff_id=uuid.uuid4(),
        )

        self.assertEqual(get_staff_schedule(self.institution, staff_id), [assignment])
