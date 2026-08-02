import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.transport.models import Route, Stop, TransportAssignment, Vehicle


class TransportTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)
        self.vehicle = Vehicle.objects.create(
            institution_id=self.institution.id, registration_number="KDA 001A", capacity=30
        )
        self.route = Route.objects.create(
            institution_id=self.institution.id, vehicle=self.vehicle, name="Route A"
        )
        self.stop = Stop.objects.create(
            institution_id=self.institution.id, route=self.route, name="Main Gate", sequence=1
        )


class VehicleConstraintTests(TransportTestCase):
    def test_registration_number_unique_per_institution(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vehicle.objects.create(
                    institution_id=self.institution.id,
                    registration_number="KDA 001A",
                    capacity=20,
                )


class StopConstraintTests(TransportTestCase):
    def test_sequence_unique_per_route(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Stop.objects.create(
                    institution_id=self.institution.id,
                    route=self.route,
                    name="Second Stop",
                    sequence=1,
                )

    def test_same_sequence_on_a_different_route_is_allowed(self):
        other_route = Route.objects.create(
            institution_id=self.institution.id, vehicle=self.vehicle, name="Route B"
        )
        Stop.objects.create(
            institution_id=self.institution.id, route=other_route, name="Market", sequence=1
        )  # must not raise


class TransportAssignmentConstraintTests(TransportTestCase):
    def test_only_one_active_assignment_per_student(self):
        student_id = uuid.uuid4()
        TransportAssignment.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            route=self.route,
            stop=self.stop,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TransportAssignment.objects.create(
                    institution_id=self.institution.id,
                    student_id=student_id,
                    route=self.route,
                    stop=self.stop,
                )
