import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.core.context import bind_institution
from apps.curriculum_844.models import ExamResult, Subject
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)
from apps.students.models import Enrollment, Student

HOSTNAME = "st-mary.educore.africa"


class Curriculum844APITestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(email="member@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.user))

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant(self, code):
        role = Role.objects.create(name="Test Role", institution=self.institution)
        permission = Permission.objects.create(code=code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.create(membership=self.membership, role=role)


class SubjectViewSetTests(Curriculum844APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_844:subject-list")

    def test_any_active_member_can_list(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 200)

    def test_create_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {"subject_catalog_id": str(uuid.uuid4()), "name": "Mathematics", "code": "MATH"},
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_844.subject.manage")

        response = self.client.post(
            self.url,
            {"subject_catalog_id": str(uuid.uuid4()), "name": "Mathematics", "code": "MATH"},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(Subject.objects.count(), 1)


class KcpeKcseResultImportViewTests(Curriculum844APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_844:kcpe-kcse-import")
        with bind_institution(self.institution):
            self.subject = Subject.objects.create(
                institution_id=self.institution.id,
                subject_catalog_id=uuid.uuid4(),
                name="Mathematics",
                code="MATH",
            )

    def test_denied_without_permission(self):
        response = self.client.post(
            self.url,
            {
                "term_id": str(uuid.uuid4()),
                "rows": [
                    {
                        "student_id": str(uuid.uuid4()),
                        "subject_id": str(self.subject.id),
                        "score": "78.00",
                        "max_score": "100.00",
                    }
                ],
            },
            format="json",
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_import_with_permission_succeeds(self):
        self._grant("curriculum_844.kcpe_kcse_result.import")

        response = self.client.post(
            self.url,
            {
                "term_id": str(uuid.uuid4()),
                "rows": [
                    {
                        "student_id": str(uuid.uuid4()),
                        "subject_id": str(self.subject.id),
                        "score": "78.00",
                        "max_score": "100.00",
                    }
                ],
            },
            format="json",
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["created"], 1)
        with bind_institution(self.institution):
            self.assertEqual(
                ExamResult.objects.filter(exam_type=ExamResult.ExamType.KCPE_KCSE).count(), 1
            )


class RecomputeMeanGradesViewTests(Curriculum844APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_844:recompute-mean-grades")
        with bind_institution(self.institution):
            self.student = Student.objects.create(
                institution_id=self.institution.id,
                admission_number="ADM-1",
                first_name="A",
                last_name="B",
            )
            self.class_grade_id = uuid.uuid4()
            self.term_id = uuid.uuid4()
            Enrollment.objects.create(
                institution_id=self.institution.id,
                student=self.student,
                class_grade_id=self.class_grade_id,
                term_id=self.term_id,
            )

    def test_denied_without_permission(self):
        response = self.client.post(
            self.url,
            {"term_id": str(self.term_id), "class_grade_id": str(self.class_grade_id)},
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_enqueues_with_permission(self):
        self._grant("curriculum_844.mean_grade.recompute")

        response = self.client.post(
            self.url,
            {"term_id": str(self.term_id), "class_grade_id": str(self.class_grade_id)},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 202)
