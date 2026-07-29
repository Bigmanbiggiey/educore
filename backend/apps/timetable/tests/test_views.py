import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.core.context import bind_institution
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)
from apps.timetable.models import Period, Timetable

HOSTNAME = "st-mary.educore.africa"


class TimetableAPITestCase(APITestCase):
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


class TimetableViewSetTests(TimetableAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:timetable:timetable-list")

    def test_create_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {"term_id": str(uuid.uuid4()), "class_grade_id": str(uuid.uuid4())},
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("timetable.timetable.manage")

        response = self.client.post(
            self.url,
            {"term_id": str(uuid.uuid4()), "class_grade_id": str(uuid.uuid4())},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(Timetable.objects.count(), 1)


class PeriodNestedViewSetTests(TimetableAPITestCase):
    def setUp(self):
        super().setUp()
        with bind_institution(self.institution):
            self.timetable = Timetable.objects.create(
                institution_id=self.institution.id,
                term_id=uuid.uuid4(),
                class_grade_id=uuid.uuid4(),
            )
        self.url = reverse(
            "v1:timetable:timetable-periods-list", kwargs={"timetable_pk": self.timetable.pk}
        )

    def test_create_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {"day_of_week": 0, "start_time": "08:00", "end_time": "09:00"},
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds_and_scopes_to_the_parent_timetable(self):
        self._grant("timetable.period.manage")

        response = self.client.post(
            self.url,
            {"day_of_week": 0, "start_time": "08:00", "end_time": "09:00"},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            period = Period.objects.get()
        self.assertEqual(period.timetable_id, self.timetable.id)

    def test_list_only_returns_periods_for_this_timetable(self):
        with bind_institution(self.institution):
            other_timetable = Timetable.objects.create(
                institution_id=self.institution.id,
                term_id=uuid.uuid4(),
                class_grade_id=uuid.uuid4(),
            )
            Period.objects.create(
                institution_id=self.institution.id,
                timetable=self.timetable,
                day_of_week=0,
                start_time="08:00",
                end_time="09:00",
            )
            Period.objects.create(
                institution_id=self.institution.id,
                timetable=other_timetable,
                day_of_week=0,
                start_time="08:00",
                end_time="09:00",
            )

        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)


class SubjectSlotAssignmentViewSetTests(TimetableAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:timetable:subject-slot-assignment-list")
        with bind_institution(self.institution):
            timetable = Timetable.objects.create(
                institution_id=self.institution.id,
                term_id=uuid.uuid4(),
                class_grade_id=uuid.uuid4(),
            )
            self.period = Period.objects.create(
                institution_id=self.institution.id,
                timetable=timetable,
                day_of_week=0,
                start_time="08:00",
                end_time="09:00",
            )

    def test_create_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {
                "period": str(self.period.id),
                "subject_id": str(uuid.uuid4()),
                "staff_id": str(uuid.uuid4()),
            },
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("timetable.subject_slot_assignment.manage")

        response = self.client.post(
            self.url,
            {
                "period": str(self.period.id),
                "subject_id": str(uuid.uuid4()),
                "staff_id": str(uuid.uuid4()),
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)

    def test_a_clashing_assignment_is_rejected_with_a_validation_error(self):
        self._grant("timetable.subject_slot_assignment.manage")
        staff_id = uuid.uuid4()
        with bind_institution(self.institution):
            other_period = Period.objects.create(
                institution_id=self.institution.id,
                timetable=self.period.timetable,
                day_of_week=0,
                start_time="08:30",
                end_time="09:30",
            )
        self.client.post(
            self.url,
            {
                "period": str(self.period.id),
                "subject_id": str(uuid.uuid4()),
                "staff_id": str(staff_id),
            },
            HTTP_HOST=HOSTNAME,
        )

        response = self.client.post(
            self.url,
            {
                "period": str(other_period.id),
                "subject_id": str(uuid.uuid4()),
                "staff_id": str(staff_id),
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 400)
