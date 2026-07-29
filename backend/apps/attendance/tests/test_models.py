import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.attendance.models import AttendanceRecord
from apps.core.context import bind_institution
from apps.institutions.models import Institution


class AttendanceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)


class AttendanceRecordConstraintTests(AttendanceTestCase):
    def test_unique_per_term_date_subject_type_target(self):
        term_id = uuid.uuid4()
        target_id = uuid.uuid4()
        AttendanceRecord.objects.create(
            institution_id=self.institution.id,
            term_id=term_id,
            date="2026-01-05",
            subject_type=AttendanceRecord.SubjectType.STUDENT,
            target_id=target_id,
            status=AttendanceRecord.Status.PRESENT,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AttendanceRecord.objects.create(
                    institution_id=self.institution.id,
                    term_id=term_id,
                    date="2026-01-05",
                    subject_type=AttendanceRecord.SubjectType.STUDENT,
                    target_id=target_id,
                    status=AttendanceRecord.Status.ABSENT,
                )

    def test_same_target_on_a_different_date_is_allowed(self):
        term_id = uuid.uuid4()
        target_id = uuid.uuid4()
        AttendanceRecord.objects.create(
            institution_id=self.institution.id,
            term_id=term_id,
            date="2026-01-05",
            subject_type=AttendanceRecord.SubjectType.STUDENT,
            target_id=target_id,
            status=AttendanceRecord.Status.PRESENT,
        )
        AttendanceRecord.objects.create(
            institution_id=self.institution.id,
            term_id=term_id,
            date="2026-01-06",
            subject_type=AttendanceRecord.SubjectType.STUDENT,
            target_id=target_id,
            status=AttendanceRecord.Status.PRESENT,
        )  # must not raise

    def test_same_target_id_for_different_subject_types_is_allowed(self):
        # UUID collision across a Student and a StaffProfile is astronomically
        # unlikely in practice, but the constraint includes subject_type
        # specifically so it's not relied upon.
        term_id = uuid.uuid4()
        target_id = uuid.uuid4()
        AttendanceRecord.objects.create(
            institution_id=self.institution.id,
            term_id=term_id,
            date="2026-01-05",
            subject_type=AttendanceRecord.SubjectType.STUDENT,
            target_id=target_id,
            status=AttendanceRecord.Status.PRESENT,
        )
        AttendanceRecord.objects.create(
            institution_id=self.institution.id,
            term_id=term_id,
            date="2026-01-05",
            subject_type=AttendanceRecord.SubjectType.STAFF,
            target_id=target_id,
            status=AttendanceRecord.Status.PRESENT,
        )  # must not raise
