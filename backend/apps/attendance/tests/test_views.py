import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.attendance.models import AttendanceRecord
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


class AttendanceAPITestCase(APITestCase):
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
        self.url = reverse("v1:attendance:attendance-record-list")

    def _bearer(self, user):
        return f"Bearer {RefreshToken.for_user(user).access_token}"

    def _grant(self, code):
        role = Role.objects.create(name="Test Role", institution=self.institution)
        permission = Permission.objects.create(code=code)
        RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.create(membership=self.membership, role=role)


class AttendanceRecordViewSetTests(AttendanceAPITestCase):
    def test_create_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {
                "term_id": str(uuid.uuid4()),
                "date": "2026-01-05",
                "subject_type": "student",
                "target_id": str(uuid.uuid4()),
                "status": "present",
            },
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("attendance.attendance_record.manage")

        response = self.client.post(
            self.url,
            {
                "term_id": str(uuid.uuid4()),
                "date": "2026-01-05",
                "subject_type": "student",
                "target_id": str(uuid.uuid4()),
                "status": "present",
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(AttendanceRecord.objects.count(), 1)

    def test_remarking_the_same_day_updates_in_place(self):
        self._grant("attendance.attendance_record.manage")
        term_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())
        payload = {
            "term_id": term_id,
            "date": "2026-01-05",
            "subject_type": "student",
            "target_id": target_id,
            "status": "absent",
        }
        self.client.post(self.url, payload, HTTP_HOST=HOSTNAME)

        payload["status"] = "present"
        response = self.client.post(self.url, payload, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(AttendanceRecord.objects.count(), 1)
            self.assertEqual(AttendanceRecord.objects.first().status, "present")

    def test_filter_by_date(self):
        self._grant("attendance.attendance_record.manage")
        with bind_institution(self.institution):
            AttendanceRecord.objects.create(
                institution_id=self.institution.id,
                term_id=uuid.uuid4(),
                date="2026-01-05",
                subject_type=AttendanceRecord.SubjectType.STUDENT,
                target_id=uuid.uuid4(),
                status=AttendanceRecord.Status.PRESENT,
            )
            AttendanceRecord.objects.create(
                institution_id=self.institution.id,
                term_id=uuid.uuid4(),
                date="2026-01-06",
                subject_type=AttendanceRecord.SubjectType.STUDENT,
                target_id=uuid.uuid4(),
                status=AttendanceRecord.Status.PRESENT,
            )

        response = self.client.get(self.url, {"date": "2026-01-05"}, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
