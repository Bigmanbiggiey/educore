from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.classes_streams.services import (
    create_academic_year,
    create_class_grade,
    create_term,
    set_current_term,
)
from apps.institutions.models import Domain
from apps.institutions.services import provision_institution
from apps.permissions.models import InstitutionMembership, MembershipRole, Role
from apps.staff.services import create_staff_profile
from apps.students.services import add_guardian, create_student, enroll_student

HOSTNAME = "st-mary-dashboard.educore.africa"


class DashboardAPITestCase(APITestCase):
    def setUp(self):
        self.institution = provision_institution(
            name="St Mary", slug="st-mary-dashboard", curriculum_types=["cbc"]
        )
        Domain.objects.filter(institution=self.institution, is_primary=True).update(
            hostname=HOSTNAME
        )
        academic_year = create_academic_year(
            institution=self.institution,
            year_label="2026",
            start_date="2026-01-01",
            end_date="2026-12-01",
        )
        self.term = create_term(
            institution=self.institution,
            academic_year=academic_year,
            name="Term 1",
            start_date="2026-01-01",
            end_date="2026-04-01",
        )
        set_current_term(institution=self.institution, term=self.term)
        self.class_grade = create_class_grade(
            institution=self.institution, term=self.term, name="Form 1", curriculum_type="cbc"
        )

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _user_with_role(self, email, role_name):
        user = User.objects.create_user(email=email, password="x" * 12)
        membership = InstitutionMembership.objects.create(user=user, institution=self.institution)
        role = Role.objects.get(name=role_name, institution=None)
        MembershipRole.objects.create(membership=membership, role=role)
        return user


class PrincipalDashboardViewTests(DashboardAPITestCase):
    def test_denied_without_the_principal_role(self):
        user = self._user_with_role("teacher@stmary.ac.ke", "Teacher")
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(user))

        response = self.client.get(reverse("v1:dashboard:principal"), HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 403)

    def test_accessible_to_the_principal_role(self):
        user = self._user_with_role("principal@stmary.ac.ke", "Principal")
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(user))

        response = self.client.get(reverse("v1:dashboard:principal"), HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertIn("class_count", response.data)


class TeacherDashboardViewTests(DashboardAPITestCase):
    def test_returns_the_teachers_own_schedule(self):
        user = self._user_with_role("teacher@stmary.ac.ke", "Teacher")
        create_staff_profile(
            institution=self.institution,
            user_id=user.id,
            employee_number="T-001",
            first_name="Ann",
            last_name="Teacher",
            employment_type="full_time",
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(user))

        response = self.client.get(reverse("v1:dashboard:teacher"), HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["schedule"], [])

    def test_404s_when_the_teacher_has_no_staff_profile(self):
        user = self._user_with_role("noprofile@stmary.ac.ke", "Teacher")
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(user))

        response = self.client.get(reverse("v1:dashboard:teacher"), HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 404)


class ParentDashboardViewTests(DashboardAPITestCase):
    def test_returns_only_the_callers_own_children(self):
        parent = self._user_with_role("parent@stmary.ac.ke", "Parent")
        student = create_student(
            institution=self.institution,
            admission_number="A-001",
            first_name="Kid",
            last_name="One",
        )
        enroll_student(
            institution=self.institution,
            student=student,
            class_grade_id=self.class_grade.id,
            term_id=self.term.id,
        )
        add_guardian(
            institution=self.institution,
            student=student,
            guardian_user_id=parent.id,
            relationship_type="parent",
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(parent))

        response = self.client.get(reverse("v1:dashboard:parent"), HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["children"]), 1)
        self.assertEqual(response.data["children"][0]["student_id"], student.id)


class StudentDashboardViewTests(DashboardAPITestCase):
    def test_404s_when_the_user_has_no_student_record(self):
        user = self._user_with_role("nostudent@stmary.ac.ke", "Student")
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(user))

        response = self.client.get(reverse("v1:dashboard:student"), HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 404)

    def test_returns_the_students_own_dashboard(self):
        user = self._user_with_role("student@stmary.ac.ke", "Student")
        student = create_student(
            institution=self.institution,
            admission_number="A-002",
            first_name="Kid",
            last_name="Two",
            user_id=user.id,
        )
        enroll_student(
            institution=self.institution,
            student=student,
            class_grade_id=self.class_grade.id,
            term_id=self.term.id,
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(user))

        response = self.client.get(reverse("v1:dashboard:student"), HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["attendance_rate"])
