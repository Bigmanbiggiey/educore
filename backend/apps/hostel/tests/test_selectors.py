import uuid

from django.test import TestCase

from apps.core.context import bind_institution
from apps.hostel.models import Hostel, Room
from apps.hostel.selectors import get_allocation_for_student, get_occupancy
from apps.hostel.services import allocate_bed
from apps.institutions.models import Institution


class HostelSelectorTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)
        self.hostel = Hostel.objects.create(institution_id=self.institution.id, name="Block A")
        self.room = Room.objects.create(
            institution_id=self.institution.id, hostel=self.hostel, room_number="101", capacity=2
        )
        self.term_id = uuid.uuid4()


class GetOccupancyTests(HostelSelectorTestCase):
    def test_reflects_current_allocations_against_capacity(self):
        allocate_bed(
            institution=self.institution,
            room=self.room,
            student_id=uuid.uuid4(),
            term_id=self.term_id,
        )

        occupancy = get_occupancy(self.institution, self.room.id, self.term_id)

        self.assertEqual(occupancy, {"capacity": 2, "occupied": 1, "available": 1})

    def test_a_different_term_has_no_occupancy(self):
        allocate_bed(
            institution=self.institution,
            room=self.room,
            student_id=uuid.uuid4(),
            term_id=self.term_id,
        )

        occupancy = get_occupancy(self.institution, self.room.id, uuid.uuid4())

        self.assertEqual(occupancy, {"capacity": 2, "occupied": 0, "available": 2})


class GetAllocationForStudentTests(HostelSelectorTestCase):
    def test_returns_none_when_unallocated(self):
        self.assertIsNone(get_allocation_for_student(self.institution, uuid.uuid4(), self.term_id))

    def test_returns_the_students_allocation(self):
        student_id = uuid.uuid4()
        allocate_bed(
            institution=self.institution,
            room=self.room,
            student_id=student_id,
            term_id=self.term_id,
        )

        allocation = get_allocation_for_student(self.institution, student_id, self.term_id)

        self.assertEqual(allocation.room_id, self.room.id)
