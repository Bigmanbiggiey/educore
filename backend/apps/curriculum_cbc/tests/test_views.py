import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.core.context import bind_institution
from apps.curriculum_cbc.models import Competency, LearningArea
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"


class CurriculumCbcAPITestCase(APITestCase):
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


class LearningAreaViewSetTests(CurriculumCbcAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_cbc:learning-area-list")

    def test_any_active_member_can_list(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 200)

    def test_create_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {
                "subject_catalog_id": str(uuid.uuid4()),
                "name": "Environmental Activities",
                "code": "ENV",
            },
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_cbc.learning_area.manage")

        response = self.client.post(
            self.url,
            {
                "subject_catalog_id": str(uuid.uuid4()),
                "name": "Environmental Activities",
                "code": "ENV",
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(LearningArea.objects.count(), 1)


class CompetencyViewSetTests(CurriculumCbcAPITestCase):
    def setUp(self):
        super().setUp()
        with bind_institution(self.institution):
            self.learning_area = LearningArea.objects.create(
                institution_id=self.institution.id,
                subject_catalog_id=uuid.uuid4(),
                name="Environmental Activities",
                code="ENV",
            )
        self.url = reverse("v1:curriculum_cbc:competency-list")

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_cbc.competency.manage")

        response = self.client.post(
            self.url,
            {
                "learning_area": str(self.learning_area.id),
                "strand": "Weather",
                "sub_strand": "Rain",
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)


class CoreValueViewSetTests(CurriculumCbcAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_cbc:core-value-list")

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_cbc.core_value.manage")

        response = self.client.post(self.url, {"name": "Respect"}, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 201)


class PCIViewSetTests(CurriculumCbcAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_cbc:pci-list")

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_cbc.pci.manage")

        response = self.client.post(
            self.url, {"name": "Environmental degradation"}, HTTP_HOST=HOSTNAME
        )

        self.assertEqual(response.status_code, 201)


class ProjectViewSetTests(CurriculumCbcAPITestCase):
    def setUp(self):
        super().setUp()
        with bind_institution(self.institution):
            learning_area = LearningArea.objects.create(
                institution_id=self.institution.id,
                subject_catalog_id=uuid.uuid4(),
                name="Environmental Activities",
                code="ENV",
            )
            self.competency = Competency.objects.create(
                institution_id=self.institution.id, learning_area=learning_area, strand="Weather"
            )
        self.url = reverse("v1:curriculum_cbc:project-list")

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_cbc.project.manage")

        response = self.client.post(
            self.url,
            {
                "student_id": str(uuid.uuid4()),
                "competency": str(self.competency.id),
                "term_id": str(uuid.uuid4()),
                "description": "Weather chart",
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
