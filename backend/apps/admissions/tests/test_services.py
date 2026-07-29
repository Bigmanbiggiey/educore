import uuid

from django.test import TestCase

from apps.admissions.models import Application
from apps.admissions.services import (
    accept_offer,
    convert_to_enrollment,
    make_offer,
    submit_application,
)
from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.students.models import Enrollment, Student


class AdmissionsServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def _application(self, **details):
        return submit_application(
            institution=self.institution,
            applicant_details={"first_name": "Amina", "last_name": "Otieno", **details},
            term_applying_for_id=uuid.uuid4(),
        )


class SubmitApplicationTests(AdmissionsServiceTestCase):
    def test_creates_the_application_and_a_history_row(self):
        application = self._application()
        self.assertEqual(application.stage, Application.Stage.SUBMITTED)
        with bind_institution(self.institution):
            self.assertEqual(application.stage_history.count(), 1)
            self.assertEqual(application.stage_history.first().stage, Application.Stage.SUBMITTED)


class MakeOfferTests(AdmissionsServiceTestCase):
    def test_creates_an_offer_and_advances_the_stage(self):
        application = self._application()

        offer = make_offer(institution=self.institution, application=application)

        application.refresh_from_db()
        self.assertIsNotNone(offer.offered_at)
        self.assertIsNone(offer.accepted_at)
        self.assertEqual(application.stage, Application.Stage.OFFERED)


class AcceptOfferTests(AdmissionsServiceTestCase):
    def test_sets_accepted_at_and_advances_the_stage(self):
        application = self._application()
        offer = make_offer(institution=self.institution, application=application)

        accepted = accept_offer(institution=self.institution, offer=offer)

        application.refresh_from_db()
        self.assertIsNotNone(accepted.accepted_at)
        self.assertEqual(application.stage, Application.Stage.ACCEPTED)


class ConvertToEnrollmentTests(AdmissionsServiceTestCase):
    def test_rejects_an_application_that_has_not_been_accepted(self):
        application = self._application()
        with self.assertRaises(ValueError):
            convert_to_enrollment(
                institution=self.institution,
                application=application,
                admission_number="ADM-001",
                class_grade_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
            )

    def test_creates_a_student_and_enrollment_from_an_accepted_application(self):
        application = self._application(
            first_name="Amina", last_name="Otieno", date_of_birth="2015-03-10", gender="female"
        )
        offer = make_offer(institution=self.institution, application=application)
        accept_offer(institution=self.institution, offer=offer)
        class_grade_id = uuid.uuid4()
        term_id = uuid.uuid4()

        enrollment = convert_to_enrollment(
            institution=self.institution,
            application=application,
            admission_number="ADM-001",
            class_grade_id=class_grade_id,
            term_id=term_id,
        )

        application.refresh_from_db()
        self.assertEqual(application.stage, Application.Stage.ENROLLED)
        self.assertEqual(enrollment.class_grade_id, class_grade_id)
        self.assertEqual(enrollment.term_id, term_id)
        with bind_institution(self.institution):
            student = Student.objects.get(admission_number="ADM-001")
            self.assertEqual(student.first_name, "Amina")
            self.assertEqual(student.last_name, "Otieno")
            self.assertEqual(Enrollment.objects.filter(student=student).count(), 1)
