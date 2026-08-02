import uuid

from django.test import TestCase

from apps.core.context import bind_institution
from apps.hostel.models import BedAllocation, Hostel, Room
from apps.hostel.services import allocate_bed
from apps.institutions.models import Institution


class HostelServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        with bind_institution(self.institution):
            self.hostel = Hostel.objects.create(institution_id=self.institution.id, name="Block A")
            self.room = Room.objects.create(
                institution_id=self.institution.id,
                hostel=self.hostel,
                room_number="101",
                capacity=2,
            )
        self.term_id = uuid.uuid4()


class AllocateBedTests(HostelServiceTestCase):
    def test_allocates_a_bed_when_under_capacity(self):
        allocation = allocate_bed(
            institution=self.institution,
            room=self.room,
            student_id=uuid.uuid4(),
            term_id=self.term_id,
        )
        self.assertEqual(allocation.room_id, self.room.id)

    def test_rejects_allocation_once_the_room_is_at_capacity(self):
        allocate_bed(
            institution=self.institution,
            room=self.room,
            student_id=uuid.uuid4(),
            term_id=self.term_id,
        )
        allocate_bed(
            institution=self.institution,
            room=self.room,
            student_id=uuid.uuid4(),
            term_id=self.term_id,
        )

        with self.assertRaises(ValueError):
            allocate_bed(
                institution=self.institution,
                room=self.room,
                student_id=uuid.uuid4(),
                term_id=self.term_id,
            )

    def test_rejects_a_duplicate_allocation_for_the_same_student_and_term(self):
        student_id = uuid.uuid4()
        allocate_bed(
            institution=self.institution,
            room=self.room,
            student_id=student_id,
            term_id=self.term_id,
        )

        with self.assertRaises(ValueError):
            allocate_bed(
                institution=self.institution,
                room=self.room,
                student_id=student_id,
                term_id=self.term_id,
            )

        # The failed attempt's savepoint rolled back cleanly — the
        # transaction is still usable for further queries, and no
        # second row was written.
        with bind_institution(self.institution):
            self.assertEqual(BedAllocation.objects.filter(student_id=student_id).count(), 1)

    def test_a_room_freed_up_in_a_different_term_does_not_count_against_capacity(self):
        allocate_bed(
            institution=self.institution,
            room=self.room,
            student_id=uuid.uuid4(),
            term_id=self.term_id,
        )
        allocate_bed(
            institution=self.institution,
            room=self.room,
            student_id=uuid.uuid4(),
            term_id=self.term_id,
        )

        # Room is full for `self.term_id`, but a different term has no
        # allocations yet.
        allocation = allocate_bed(
            institution=self.institution,
            room=self.room,
            student_id=uuid.uuid4(),
            term_id=uuid.uuid4(),
        )
        self.assertIsNotNone(allocation.id)
