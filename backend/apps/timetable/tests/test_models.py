import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.timetable.models import Period, SubjectSlotAssignment, Timetable


class TimetableTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

    def _timetable(self):
        return Timetable.objects.create(
            institution_id=self.institution.id, term_id=uuid.uuid4(), class_grade_id=uuid.uuid4()
        )

    def _period(self, timetable=None, day_of_week=0, start_time="08:00", end_time="09:00"):
        return Period.objects.create(
            institution_id=self.institution.id,
            timetable=timetable or self._timetable(),
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
        )


class TimetableConstraintTests(TimetableTestCase):
    def test_unique_per_institution_term_class(self):
        term_id = uuid.uuid4()
        class_grade_id = uuid.uuid4()
        Timetable.objects.create(
            institution_id=self.institution.id, term_id=term_id, class_grade_id=class_grade_id
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Timetable.objects.create(
                    institution_id=self.institution.id,
                    term_id=term_id,
                    class_grade_id=class_grade_id,
                )


class PeriodConstraintTests(TimetableTestCase):
    def test_start_before_end_is_enforced(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._period(start_time="09:00", end_time="08:00")

    def test_unique_start_per_timetable_day(self):
        timetable = self._timetable()
        self._period(timetable=timetable, day_of_week=0, start_time="08:00", end_time="09:00")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._period(
                    timetable=timetable, day_of_week=0, start_time="08:00", end_time="10:00"
                )

    def test_same_start_time_on_a_different_day_is_allowed(self):
        timetable = self._timetable()
        self._period(timetable=timetable, day_of_week=0, start_time="08:00", end_time="09:00")
        self._period(
            timetable=timetable, day_of_week=1, start_time="08:00", end_time="09:00"
        )  # must not raise


class SubjectSlotAssignmentConstraintTests(TimetableTestCase):
    def test_one_assignment_per_period(self):
        period = self._period()
        SubjectSlotAssignment.objects.create(
            institution_id=self.institution.id,
            period=period,
            subject_id=uuid.uuid4(),
            staff_id=uuid.uuid4(),
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SubjectSlotAssignment.objects.create(
                    institution_id=self.institution.id,
                    period=period,
                    subject_id=uuid.uuid4(),
                    staff_id=uuid.uuid4(),
                )
