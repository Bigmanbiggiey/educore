import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.analytics.models import AttendanceRateSnapshot
from apps.core.context import bind_institution
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"


class AnalyticsAPITestCase(APITestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        Domain.objects.create(
            institution=self.institution,
            hostname=HOSTNAME,
            domain_type=Domain.DomainType.SUBDOMAIN,
            is_primary=True,
        )
        self.user = User.objects.create_user(email="principal@stmary.ac.ke", password="x" * 12)
        self.membership = InstitutionMembership.objects.create(
            user=self.user, institution=self.institution
        )
        self.client.credentials(HTTP_AUTHORIZATION=self._bearer(self.user))

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant(self, code):
        role, _ = Role.objects.get_or_create(name="Test Role", institution=self.institution)
        permission = Permission.objects.create(code=code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.get_or_create(membership=self.membership, role=role)


class AttendanceRateSnapshotViewSetTests(AnalyticsAPITestCase):
    def test_any_active_member_can_read(self):
        response = self.client.get(
            reverse("v1:analytics:attendance-rollup-list"), HTTP_HOST=HOSTNAME
        )
        self.assertEqual(response.status_code, 200)

    def test_writes_are_not_exposed_at_all(self):
        response = self.client.post(
            reverse("v1:analytics:attendance-rollup-list"),
            {"class_grade_id": str(uuid.uuid4()), "term_id": str(uuid.uuid4()), "rate": "0.9"},
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 405)

    def test_filters_by_class_grade_and_term(self):
        class_grade_id = uuid.uuid4()
        term_id = uuid.uuid4()
        with bind_institution(self.institution):
            AttendanceRateSnapshot.objects.create(
                institution_id=self.institution.id,
                class_grade_id=class_grade_id,
                term_id=term_id,
                rate="0.9",
            )
            AttendanceRateSnapshot.objects.create(
                institution_id=self.institution.id,
                class_grade_id=uuid.uuid4(),
                term_id=term_id,
                rate="0.5",
            )

        response = self.client.get(
            reverse("v1:analytics:attendance-rollup-list"),
            {"class_grade_id": str(class_grade_id)},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)


class RecomputeRollupsViewTests(AnalyticsAPITestCase):
    def test_recompute_without_permission_is_denied(self):
        response = self.client.post(
            reverse("v1:analytics:recompute-rollups"),
            {"class_grade_id": str(uuid.uuid4()), "term_id": str(uuid.uuid4())},
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_recompute_with_permission_enqueues_the_task(self):
        self._grant("analytics.rollup.recompute")

        response = self.client.post(
            reverse("v1:analytics:recompute-rollups"),
            {"class_grade_id": str(uuid.uuid4()), "term_id": str(uuid.uuid4())},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 202)
