import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.core.context import bind_institution
from apps.curriculum_tvet.models import Certificate, Course, IndustrialAttachment, TVETDepartment
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"


class CurriculumTvetAPITestCase(APITestCase):
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


class TVETDepartmentViewSetTests(CurriculumTvetAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_tvet:department-list")

    def test_any_active_member_can_list(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 200)

    def test_create_without_permission_is_denied(self):
        response = self.client.post(self.url, {"name": "Engineering"}, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_tvet.department.manage")

        response = self.client.post(self.url, {"name": "Engineering"}, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(TVETDepartment.objects.count(), 1)


class CourseViewSetTests(CurriculumTvetAPITestCase):
    def setUp(self):
        super().setUp()
        with bind_institution(self.institution):
            self.department = TVETDepartment.objects.create(
                institution_id=self.institution.id, name="Engineering"
            )
        self.url = reverse("v1:curriculum_tvet:course-list")

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_tvet.course.manage")

        response = self.client.post(
            self.url,
            {
                "department": str(self.department.id),
                "course_code": "ENG101",
                "name": "Automotive Engineering",
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(Course.objects.count(), 1)


class IndustrialAttachmentViewSetTests(CurriculumTvetAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_tvet:industrial-attachment-list")

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_tvet.industrial_attachment.manage")

        response = self.client.post(
            self.url,
            {
                "student_id": str(uuid.uuid4()),
                "host_organization": "Acme Motors",
                "start_date": "2026-01-01",
                "end_date": "2026-03-01",
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(IndustrialAttachment.objects.count(), 1)


class CertificateViewSetTests(CurriculumTvetAPITestCase):
    def setUp(self):
        super().setUp()
        with bind_institution(self.institution):
            department = TVETDepartment.objects.create(
                institution_id=self.institution.id, name="Engineering"
            )
            self.course = Course.objects.create(
                institution_id=self.institution.id,
                department=department,
                course_code="ENG101",
                name="Automotive Engineering",
            )
        self.url = reverse("v1:curriculum_tvet:certificate-list")

    def test_create_with_permission_succeeds_and_defaults_issued_at(self):
        self._grant("curriculum_tvet.certificate.manage")

        response = self.client.post(
            self.url,
            {
                "student_id": str(uuid.uuid4()),
                "course": str(self.course.id),
                "certificate_number": "CERT-001",
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data["issued_at"])
        with bind_institution(self.institution):
            self.assertEqual(Certificate.objects.count(), 1)
