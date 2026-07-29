import uuid

from django.test import TestCase

from apps.attendance.models import AttendanceRecord
from apps.attendance.services import mark_attendance
from apps.core.context import bind_institution
from apps.institutions.models import Institution


class AttendanceServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")


class MarkAttendanceTests(AttendanceServiceTestCase):
    def test_creates_a_new_record(self):
        target_id = uuid.uuid4()
        record = mark_attendance(
            institution=self.institution,
            term_id=uuid.uuid4(),
            date="2026-01-05",
            subject_type=AttendanceRecord.SubjectType.STUDENT,
            target_id=target_id,
            status=AttendanceRecord.Status.PRESENT,
        )
        self.assertEqual(record.target_id, target_id)
        self.assertEqual(record.status, AttendanceRecord.Status.PRESENT)

    def test_remarking_the_same_day_updates_rather_than_duplicates(self):
        term_id = uuid.uuid4()
        target_id = uuid.uuid4()

        mark_attendance(
            institution=self.institution,
            term_id=term_id,
            date="2026-01-05",
            subject_type=AttendanceRecord.SubjectType.STUDENT,
            target_id=target_id,
            status=AttendanceRecord.Status.ABSENT,
        )
        mark_attendance(
            institution=self.institution,
            term_id=term_id,
            date="2026-01-05",
            subject_type=AttendanceRecord.SubjectType.STUDENT,
            target_id=target_id,
            status=AttendanceRecord.Status.PRESENT,
        )

        with bind_institution(self.institution):
            self.assertEqual(AttendanceRecord.objects.count(), 1)
            self.assertEqual(
                AttendanceRecord.objects.first().status, AttendanceRecord.Status.PRESENT
            )

    def test_rejects_an_unknown_subject_type(self):
        with self.assertRaises(ValueError):
            mark_attendance(
                institution=self.institution,
                term_id=uuid.uuid4(),
                date="2026-01-05",
                subject_type="klingon",
                target_id=uuid.uuid4(),
                status=AttendanceRecord.Status.PRESENT,
            )

    def test_rejects_an_unknown_status(self):
        with self.assertRaises(ValueError):
            mark_attendance(
                institution=self.institution,
                term_id=uuid.uuid4(),
                date="2026-01-05",
                subject_type=AttendanceRecord.SubjectType.STUDENT,
                target_id=uuid.uuid4(),
                status="klingon",
            )
