import uuid

from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.transport.models import Route, Stop, TransportAssignment, Vehicle
from apps.transport.services import assign_transport


class TransportServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        with bind_institution(self.institution):
            self.vehicle = Vehicle.objects.create(
                institution_id=self.institution.id, registration_number="KDA 001A", capacity=30
            )
            self.route = Route.objects.create(
                institution_id=self.institution.id, vehicle=self.vehicle, name="Route A"
            )
            self.stop_a = Stop.objects.create(
                institution_id=self.institution.id, route=self.route, name="Gate", sequence=1
            )
            self.stop_b = Stop.objects.create(
                institution_id=self.institution.id, route=self.route, name="Market", sequence=2
            )


class AssignTransportTests(TransportServiceTestCase):
    def test_creates_a_new_assignment(self):
        student_id = uuid.uuid4()
        assignment = assign_transport(
            institution=self.institution, student_id=student_id, route=self.route, stop=self.stop_a
        )
        self.assertEqual(assignment.stop_id, self.stop_a.id)

    def test_reassigning_the_same_student_updates_in_place(self):
        student_id = uuid.uuid4()
        assign_transport(
            institution=self.institution, student_id=student_id, route=self.route, stop=self.stop_a
        )
        assign_transport(
            institution=self.institution, student_id=student_id, route=self.route, stop=self.stop_b
        )

        with bind_institution(self.institution):
            self.assertEqual(TransportAssignment.objects.filter(student_id=student_id).count(), 1)
            self.assertEqual(
                TransportAssignment.objects.get(student_id=student_id).stop_id, self.stop_b.id
            )
