import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.students.models import Enrollment, GuardianRelationship, Student


class StudentsTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

    def _student(self, **kwargs):
        defaults = {
            "institution_id": self.institution.id,
            "admission_number": "ADM-001",
            "first_name": "Jane",
            "last_name": "Doe",
        }
        defaults.update(kwargs)
        return Student.objects.create(**defaults)


class StudentConstraintTests(StudentsTestCase):
    def test_unique_admission_number_per_institution(self):
        self._student(admission_number="ADM-001")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._student(admission_number="ADM-001")

    def test_soft_delete_hides_but_does_not_remove(self):
        student = self._student()
        student.delete()

        self.assertEqual(list(Student.objects.all()), [])
        self.assertTrue(Student.all_objects.filter(pk=student.pk).exists())

    def test_carries_timestamps(self):
        student = self._student()
        self.assertIsNotNone(student.created_at)
        self.assertIsNotNone(student.updated_at)


class EnrollmentConstraintTests(StudentsTestCase):
    def test_unique_active_enrollment_per_student_per_term(self):
        student = self._student()
        term_id = uuid.uuid4()
        Enrollment.objects.create(
            institution_id=self.institution.id,
            student=student,
            class_grade_id=uuid.uuid4(),
            term_id=term_id,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Enrollment.objects.create(
                    institution_id=self.institution.id,
                    student=student,
                    class_grade_id=uuid.uuid4(),
                    term_id=term_id,
                )

    def test_defaults_to_active_status(self):
        student = self._student()
        enrollment = Enrollment.objects.create(
            institution_id=self.institution.id,
            student=student,
            class_grade_id=uuid.uuid4(),
            term_id=uuid.uuid4(),
        )
        self.assertEqual(enrollment.status, Enrollment.Status.ACTIVE)

    def test_soft_delete_hides_but_does_not_remove(self):
        student = self._student()
        enrollment = Enrollment.objects.create(
            institution_id=self.institution.id,
            student=student,
            class_grade_id=uuid.uuid4(),
            term_id=uuid.uuid4(),
        )
        enrollment.delete()

        self.assertEqual(list(Enrollment.objects.all()), [])
        self.assertTrue(Enrollment.all_objects.filter(pk=enrollment.pk).exists())


class GuardianRelationshipConstraintTests(StudentsTestCase):
    def test_unique_student_guardian_pair(self):
        student = self._student()
        guardian_id = uuid.uuid4()
        GuardianRelationship.objects.create(
            institution_id=self.institution.id,
            student=student,
            guardian_user_id=guardian_id,
            relationship_type=GuardianRelationship.RelationshipType.PARENT,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                GuardianRelationship.objects.create(
                    institution_id=self.institution.id,
                    student=student,
                    guardian_user_id=guardian_id,
                    relationship_type=GuardianRelationship.RelationshipType.GUARDIAN,
                )

    def test_a_student_can_have_multiple_distinct_guardians(self):
        student = self._student()
        GuardianRelationship.objects.create(
            institution_id=self.institution.id,
            student=student,
            guardian_user_id=uuid.uuid4(),
            relationship_type=GuardianRelationship.RelationshipType.PARENT,
        )
        GuardianRelationship.objects.create(
            institution_id=self.institution.id,
            student=student,
            guardian_user_id=uuid.uuid4(),
            relationship_type=GuardianRelationship.RelationshipType.PARENT,
        )  # must not raise
