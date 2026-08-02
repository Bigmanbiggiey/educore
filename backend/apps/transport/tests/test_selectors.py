import uuid

from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.transport.models import Route, Stop, Vehicle
from apps.transport.selectors import get_assignment_for_student, get_route_manifest
from apps.transport.services import assign_transport


class TransportSelectorTestCase(TestCase):
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


class GetRouteManifestTests(TransportSelectorTestCase):
    def test_returns_stops_in_sequence_order_with_assigned_students(self):
        student_a = uuid.uuid4()
        student_b = uuid.uuid4()
        assign_transport(
            institution=self.institution, student_id=student_a, route=self.route, stop=self.stop_b
        )
        assign_transport(
            institution=self.institution, student_id=student_b, route=self.route, stop=self.stop_a
        )

        manifest = get_route_manifest(self.institution, self.route.id)

        self.assertEqual([entry["name"] for entry in manifest], ["Gate", "Market"])
        self.assertEqual(manifest[0]["student_ids"], [student_b])
        self.assertEqual(manifest[1]["student_ids"], [student_a])

    def test_a_stop_with_no_assignments_has_an_empty_student_list(self):
        manifest = get_route_manifest(self.institution, self.route.id)
        self.assertEqual(manifest[0]["student_ids"], [])


class GetAssignmentForStudentTests(TransportSelectorTestCase):
    def test_returns_none_when_unassigned(self):
        self.assertIsNone(get_assignment_for_student(self.institution, uuid.uuid4()))

    def test_returns_the_students_assignment(self):
        student_id = uuid.uuid4()
        assign_transport(
            institution=self.institution, student_id=student_id, route=self.route, stop=self.stop_a
        )

        assignment = get_assignment_for_student(self.institution, student_id)

        self.assertEqual(assignment.stop_id, self.stop_a.id)
