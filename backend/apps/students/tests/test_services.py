import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.institutions.models import Institution
from apps.students.models import Enrollment, GuardianRelationship, Student
from apps.students.services import add_guardian, create_student, enroll_student


class StudentsServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def _student(self, **kwargs):
        defaults = {
            "institution": self.institution,
            "admission_number": "ADM-001",
            "first_name": "Jane",
            "last_name": "Doe",
        }
        defaults.update(kwargs)
        return create_student(**defaults)


class CreateStudentTests(StudentsServiceTestCase):
    def test_creates_and_scopes_to_institution(self):
        student = self._student()
        self.assertEqual(student.institution_id, self.institution.id)
        self.assertIsInstance(student, Student)


class EnrollStudentTests(StudentsServiceTestCase):
    def test_creates_an_active_enrollment_by_default(self):
        student = self._student()

        enrollment = enroll_student(
            institution=self.institution,
            student=student,
            class_grade_id=uuid.uuid4(),
            term_id=uuid.uuid4(),
        )

        self.assertEqual(enrollment.status, Enrollment.Status.ACTIVE)
        self.assertEqual(enrollment.student, student)

    def test_rejects_a_second_enrollment_for_the_same_term(self):
        student = self._student()
        term_id = uuid.uuid4()
        enroll_student(
            institution=self.institution,
            student=student,
            class_grade_id=uuid.uuid4(),
            term_id=term_id,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                enroll_student(
                    institution=self.institution,
                    student=student,
                    class_grade_id=uuid.uuid4(),
                    term_id=term_id,
                )


class AddGuardianTests(StudentsServiceTestCase):
    def test_creates_the_relationship(self):
        student = self._student()
        guardian_id = uuid.uuid4()

        relationship = add_guardian(
            institution=self.institution,
            student=student,
            guardian_user_id=guardian_id,
            relationship_type=GuardianRelationship.RelationshipType.PARENT,
        )

        self.assertEqual(relationship.guardian_user_id, guardian_id)

    def test_rejects_an_unknown_relationship_type(self):
        student = self._student()
        with self.assertRaises(ValueError):
            add_guardian(
                institution=self.institution,
                student=student,
                guardian_user_id=uuid.uuid4(),
                relationship_type="sibling",
            )
