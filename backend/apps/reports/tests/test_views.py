import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.classes_streams.services import create_academic_year, create_class_grade, create_term
from apps.institutions.models import Domain
from apps.institutions.services import provision_institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)
from apps.students.services import add_guardian, create_student, enroll_student

HOSTNAME = "st-mary-reports-view.educore.africa"


class ReportsAPITestCase(APITestCase):
    def setUp(self):
        self.institution = provision_institution(
            name="St Mary",
            slug="st-mary-reports-view",
            curriculum_types=["844"],
            admin_email="admin@st-mary-reports-view.ac.ke",
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
        self.class_grade = create_class_grade(
            institution=self.institution, term=self.term, name="Form 1", curriculum_type="844"
        )
        self.student = create_student(
            institution=self.institution,
            admission_number="A-001",
            first_name="Jane",
            last_name="Doe",
        )
        enroll_student(
            institution=self.institution,
            student=self.student,
            class_grade_id=self.class_grade.id,
            term_id=self.term.id,
        )
        self.staff_user = User.objects.create_user(email="staff@stmary.ac.ke", password="x" * 12)
        InstitutionMembership.objects.create(user=self.staff_user, institution=self.institution)

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant(self, user, code):
        membership = InstitutionMembership.objects.get(user=user, institution=self.institution)
        role, _ = Role.objects.get_or_create(name="Test Role", institution=self.institution)
        permission = Permission.objects.create(code=code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.get_or_create(membership=membership, role=role)

    def _assign_role(self, user, role_name):
        membership = InstitutionMembership.objects.get(user=user, institution=self.institution)
        role = Role.objects.get(name=role_name, institution=None)
        MembershipRole.objects.get_or_create(membership=membership, role=role)


class GenerateReportCardViewTests(ReportsAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:reports:generate-report-card")

    def test_any_active_member_can_generate_any_students_report(self):
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.staff_user))

        response = self.client.post(
            self.url,
            {"student_id": str(self.student.id), "term_id": str(self.term.id)},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["minio_object_key"].endswith(".pdf"))

    def test_a_parent_may_generate_their_own_childs_report(self):
        parent_user = User.objects.create_user(email="parent@stmary.ac.ke", password="x" * 12)
        InstitutionMembership.objects.create(user=parent_user, institution=self.institution)
        self._assign_role(parent_user, "Parent")
        add_guardian(
            institution=self.institution,
            student=self.student,
            guardian_user_id=parent_user.id,
            relationship_type="parent",
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(parent_user))

        response = self.client.post(
            self.url,
            {"student_id": str(self.student.id), "term_id": str(self.term.id)},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)

    def test_a_parent_may_not_generate_another_childs_report(self):
        parent_user = User.objects.create_user(email="parent2@stmary.ac.ke", password="x" * 12)
        InstitutionMembership.objects.create(user=parent_user, institution=self.institution)
        self._assign_role(parent_user, "Parent")
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(parent_user))

        response = self.client.post(
            self.url,
            {"student_id": str(self.student.id), "term_id": str(self.term.id)},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 403)

    def test_unknown_student_returns_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.staff_user))

        response = self.client.post(
            self.url,
            {"student_id": str(uuid.uuid4()), "term_id": str(self.term.id)},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 404)


class GenerateClassReportCardsViewTests(ReportsAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:reports:generate-class-report-cards")

    def test_requires_the_generate_class_permission(self):
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.staff_user))

        response = self.client.post(
            self.url,
            {"class_grade_id": str(self.class_grade.id), "term_id": str(self.term.id)},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 403)

    def test_enqueues_the_batch_task_with_permission(self):
        self._grant(self.staff_user, "reports.report_card.generate_class")
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.staff_user))

        response = self.client.post(
            self.url,
            {"class_grade_id": str(self.class_grade.id), "term_id": str(self.term.id)},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 202)
