import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.core.context import bind_institution
from apps.hostel.models import BedAllocation, Hostel, Room
from apps.institutions.models import Institution


class HostelTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)
        self.hostel = Hostel.objects.create(institution_id=self.institution.id, name="Block A")
        self.room = Room.objects.create(
            institution_id=self.institution.id, hostel=self.hostel, room_number="101", capacity=2
        )


class RoomConstraintTests(HostelTestCase):
    def test_room_number_unique_per_hostel(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Room.objects.create(
                    institution_id=self.institution.id,
                    hostel=self.hostel,
                    room_number="101",
                    capacity=4,
                )

    def test_same_room_number_in_a_different_hostel_is_allowed(self):
        other_hostel = Hostel.objects.create(institution_id=self.institution.id, name="Block B")
        Room.objects.create(
            institution_id=self.institution.id, hostel=other_hostel, room_number="101", capacity=2
        )  # must not raise


class BedAllocationConstraintTests(HostelTestCase):
    def test_only_one_allocation_per_student_per_term(self):
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        BedAllocation.objects.create(
            institution_id=self.institution.id,
            room=self.room,
            student_id=student_id,
            term_id=term_id,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BedAllocation.objects.create(
                    institution_id=self.institution.id,
                    room=self.room,
                    student_id=student_id,
                    term_id=term_id,
                )

    def test_same_student_in_a_different_term_is_allowed(self):
        student_id = uuid.uuid4()
        BedAllocation.objects.create(
            institution_id=self.institution.id,
            room=self.room,
            student_id=student_id,
            term_id=uuid.uuid4(),
        )
        BedAllocation.objects.create(
            institution_id=self.institution.id,
            room=self.room,
            student_id=student_id,
            term_id=uuid.uuid4(),
        )  # must not raise
