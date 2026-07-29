import uuid

from django.test import TestCase

from apps.core.context import bind_institution
from apps.institutions.models import Institution
from apps.students.models import Enrollment, GuardianRelationship, Student
from apps.students.selectors import (
    get_active_enrollment,
    get_active_enrollments,
    get_active_roster,
    get_guardian_children,
    get_student_by_user_id,
)


class StudentsSelectorTestCase(TestCase):
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


class GetActiveRosterTests(StudentsSelectorTestCase):
    def test_returns_only_actively_enrolled_students_in_the_class(self):
        class_grade_id = uuid.uuid4()
        active_student = self._student(admission_number="ADM-001")
        Enrollment.objects.create(
            institution_id=self.institution.id,
            student=active_student,
            class_grade_id=class_grade_id,
            term_id=uuid.uuid4(),
            status=Enrollment.Status.ACTIVE,
        )
        withdrawn_student = self._student(admission_number="ADM-002")
        Enrollment.objects.create(
            institution_id=self.institution.id,
            student=withdrawn_student,
            class_grade_id=class_grade_id,
            term_id=uuid.uuid4(),
            status=Enrollment.Status.WITHDRAWN,
        )
        other_class_student = self._student(admission_number="ADM-003")
        Enrollment.objects.create(
            institution_id=self.institution.id,
            student=other_class_student,
            class_grade_id=uuid.uuid4(),
            term_id=uuid.uuid4(),
            status=Enrollment.Status.ACTIVE,
        )

        roster = get_active_roster(class_grade_id)

        self.assertEqual(list(roster), [active_student])


class GetActiveEnrollmentsTests(StudentsSelectorTestCase):
    def test_returns_only_active_enrollments_for_the_class_and_term(self):
        class_grade_id = uuid.uuid4()
        term_id = uuid.uuid4()
        active_student = self._student(admission_number="ADM-001")
        active_enrollment = Enrollment.objects.create(
            institution_id=self.institution.id,
            student=active_student,
            class_grade_id=class_grade_id,
            term_id=term_id,
            status=Enrollment.Status.ACTIVE,
        )
        withdrawn_student = self._student(admission_number="ADM-002")
        Enrollment.objects.create(
            institution_id=self.institution.id,
            student=withdrawn_student,
            class_grade_id=class_grade_id,
            term_id=term_id,
            status=Enrollment.Status.WITHDRAWN,
        )
        other_term_student = self._student(admission_number="ADM-003")
        Enrollment.objects.create(
            institution_id=self.institution.id,
            student=other_term_student,
            class_grade_id=class_grade_id,
            term_id=uuid.uuid4(),
            status=Enrollment.Status.ACTIVE,
        )

        enrollments = get_active_enrollments(self.institution, class_grade_id, term_id)

        self.assertEqual(list(enrollments), [active_enrollment])


class GetGuardianChildrenTests(StudentsSelectorTestCase):
    def test_returns_only_that_guardians_children(self):
        guardian_id = uuid.uuid4()
        other_guardian_id = uuid.uuid4()
        own_child = self._student(admission_number="ADM-001")
        GuardianRelationship.objects.create(
            institution_id=self.institution.id,
            student=own_child,
            guardian_user_id=guardian_id,
            relationship_type=GuardianRelationship.RelationshipType.PARENT,
        )
        other_child = self._student(admission_number="ADM-002")
        GuardianRelationship.objects.create(
            institution_id=self.institution.id,
            student=other_child,
            guardian_user_id=other_guardian_id,
            relationship_type=GuardianRelationship.RelationshipType.PARENT,
        )

        self.assertEqual(list(get_guardian_children(guardian_id)), [own_child])

    def test_returns_empty_for_a_guardian_with_no_children(self):
        self.assertEqual(list(get_guardian_children(uuid.uuid4())), [])


class GetActiveEnrollmentTests(StudentsSelectorTestCase):
    def test_returns_the_active_enrollment_for_the_term(self):
        student = self._student()
        term_id = uuid.uuid4()
        enrollment = Enrollment.objects.create(
            institution_id=self.institution.id,
            student=student,
            class_grade_id=uuid.uuid4(),
            term_id=term_id,
        )

        self.assertEqual(get_active_enrollment(student, term_id), enrollment)

    def test_returns_none_for_a_different_term(self):
        student = self._student()
        Enrollment.objects.create(
            institution_id=self.institution.id,
            student=student,
            class_grade_id=uuid.uuid4(),
            term_id=uuid.uuid4(),
        )

        self.assertIsNone(get_active_enrollment(student, uuid.uuid4()))


class GetStudentByUserIdTests(StudentsSelectorTestCase):
    def test_returns_the_matching_student(self):
        user_id = uuid.uuid4()
        student = self._student(user_id=user_id)

        self.assertEqual(get_student_by_user_id(user_id), student)

    def test_returns_none_when_no_student_has_that_user_id(self):
        self.assertIsNone(get_student_by_user_id(uuid.uuid4()))
