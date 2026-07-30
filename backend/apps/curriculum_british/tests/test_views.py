import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.core.context import bind_institution
from apps.curriculum_british.models import PredictedGrade, Subject, YearGroup
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"


class CurriculumBritishAPITestCase(APITestCase):
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


class YearGroupViewSetTests(CurriculumBritishAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_british:year-group-list")

    def test_any_active_member_can_list(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 200)

    def test_create_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {"class_grade_id": str(uuid.uuid4()), "key_stage": "ks3", "name": "Year 7", "order": 7},
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_british.year_group.manage")

        response = self.client.post(
            self.url,
            {"class_grade_id": str(uuid.uuid4()), "key_stage": "ks3", "name": "Year 7", "order": 7},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(YearGroup.objects.count(), 1)


class SubjectViewSetTests(CurriculumBritishAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_british:subject-list")

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_british.subject.manage")

        response = self.client.post(
            self.url,
            {
                "subject_catalog_id": str(uuid.uuid4()),
                "name": "Mathematics",
                "code": "MATH",
                "qualification_level": "igcse",
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(Subject.objects.get().qualification_level, "igcse")


class PredictedGradeViewSetTests(CurriculumBritishAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_british:predicted-grade-list")
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
                "student_id": str(uuid.uuid4()),
                "subject": str(self.subject.id),
                "academic_year_id": str(uuid.uuid4()),
                "predicted_grade": "A",
            },
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_injects_set_by_from_the_request_user(self):
        self._grant("curriculum_british.predicted_grade.manage")

        response = self.client.post(
            self.url,
            {
                "student_id": str(uuid.uuid4()),
                "subject": str(self.subject.id),
                "academic_year_id": str(uuid.uuid4()),
                "predicted_grade": "A",
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["set_by"], str(self.user.id))

    def test_setting_the_same_grade_again_updates_rather_than_duplicates(self):
        self._grant("curriculum_british.predicted_grade.manage")
        student_id = str(uuid.uuid4())
        academic_year_id = str(uuid.uuid4())
        payload = {
            "student_id": student_id,
            "subject": str(self.subject.id),
            "academic_year_id": academic_year_id,
            "predicted_grade": "B",
        }
        self.client.post(self.url, payload, HTTP_HOST=HOSTNAME)

        payload["predicted_grade"] = "A*"
        response = self.client.post(self.url, payload, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(PredictedGrade.objects.count(), 1)
            self.assertEqual(PredictedGrade.objects.first().predicted_grade, "A*")
