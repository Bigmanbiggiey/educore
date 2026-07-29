import uuid

from django.test import TestCase

from apps.attendance.models import AttendanceRecord
from apps.attendance.selectors import get_attendance_rate, get_records
from apps.core.context import bind_institution
from apps.institutions.models import Institution


class AttendanceSelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

    def _mark(self, target_id, date, status, term_id=None):
        return AttendanceRecord.objects.create(
            institution_id=self.institution.id,
            term_id=term_id or uuid.uuid4(),
            date=date,
            subject_type=AttendanceRecord.SubjectType.STUDENT,
            target_id=target_id,
            status=status,
        )


class GetRecordsTests(AttendanceSelectorTestCase):
    def test_returns_only_records_for_the_target(self):
        target_id = uuid.uuid4()
        record = self._mark(target_id, "2026-01-05", AttendanceRecord.Status.PRESENT)
        self._mark(uuid.uuid4(), "2026-01-05", AttendanceRecord.Status.PRESENT)

        results = get_records(self.institution, AttendanceRecord.SubjectType.STUDENT, target_id)

        self.assertEqual(results, [record])


class GetAttendanceRateTests(AttendanceSelectorTestCase):
    def test_returns_none_when_no_records_exist(self):
        rate = get_attendance_rate(
            self.institution, AttendanceRecord.SubjectType.STUDENT, uuid.uuid4()
        )
        self.assertIsNone(rate)

    def test_counts_present_and_late_as_attended(self):
        target_id = uuid.uuid4()
        self._mark(target_id, "2026-01-05", AttendanceRecord.Status.PRESENT)
        self._mark(target_id, "2026-01-06", AttendanceRecord.Status.LATE)
        self._mark(target_id, "2026-01-07", AttendanceRecord.Status.ABSENT)
        self._mark(target_id, "2026-01-08", AttendanceRecord.Status.EXCUSED)

        rate = get_attendance_rate(
            self.institution, AttendanceRecord.SubjectType.STUDENT, target_id
        )

        self.assertEqual(rate, 0.5)

    def test_filters_by_term_when_given(self):
        target_id = uuid.uuid4()
        term_id = uuid.uuid4()
        self._mark(target_id, "2026-01-05", AttendanceRecord.Status.PRESENT, term_id=term_id)
        self._mark(target_id, "2026-04-05", AttendanceRecord.Status.ABSENT, term_id=uuid.uuid4())

        rate = get_attendance_rate(
            self.institution, AttendanceRecord.SubjectType.STUDENT, target_id, term_id=term_id
        )

        self.assertEqual(rate, 1.0)
