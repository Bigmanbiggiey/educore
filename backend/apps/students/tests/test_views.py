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
from apps.students.models import GuardianRelationship, Student

HOSTNAME = "st-mary.educore.africa"


class StudentsAPITestCase(APITestCase):
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

    def _grant_role(self, role_name, *, permission_codes=()):
        role = Role.objects.create(name=role_name, institution=self.institution)
        for code in permission_codes:
            permission = Permission.objects.create(code=code)
            RolePermission.objects.create(role=role, permission=permission)
        MembershipRole.objects.create(membership=self.membership, role=role)
        return role

    def _student(self, **kwargs):
        defaults = {
            "institution_id": self.institution.id,
            "admission_number": "ADM-001",
            "first_name": "Jane",
            "last_name": "Doe",
        }
        defaults.update(kwargs)
        with bind_institution(self.institution):
            return Student.objects.create(**defaults)


class StudentViewSetPermissionTests(StudentsAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:students:student-list")

    def test_no_permission_is_denied(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 403)

    def test_broad_permission_sees_the_whole_roster(self):
        self._grant_role("Registrar", permission_codes=["students.student.manage"])
        self._student(admission_number="ADM-001")
        self._student(admission_number="ADM-002")

        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)


class StudentViewSetObjectScopeTests(StudentsAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:students:student-list")

    def test_parent_only_sees_their_own_children_even_with_broad_permission(self):
        # Broad permission granted too — must still be scoped down, per the
        # fail-closed design (docs/permissions.md §3).
        self._grant_role("Parent", permission_codes=["students.student.manage"])
        own_child = self._student(admission_number="ADM-001")
        with bind_institution(self.institution):
            GuardianRelationship.objects.create(
                institution_id=self.institution.id,
                student=own_child,
                guardian_user_id=self.user.id,
                relationship_type=GuardianRelationship.RelationshipType.PARENT,
            )
        self._student(admission_number="ADM-002")  # not their child

        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["admission_number"], "ADM-001")

    def test_student_only_sees_their_own_record(self):
        self._grant_role("Student", permission_codes=["students.student.manage"])
        self._student(admission_number="ADM-001", user_id=self.user.id)
        self._student(admission_number="ADM-002", user_id=uuid.uuid4())

        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["admission_number"], "ADM-001")


class EnrollmentViewSetTests(StudentsAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:students:enrollment-list")

    def test_create_without_permission_is_denied(self):
        student = self._student()
        response = self.client.post(
            self.url,
            {
                "student": str(student.id),
                "class_grade_id": str(uuid.uuid4()),
                "term_id": str(uuid.uuid4()),
            },
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant_role("Registrar", permission_codes=["students.enrollment.manage"])
        student = self._student()

        response = self.client.post(
            self.url,
            {
                "student": str(student.id),
                "class_grade_id": str(uuid.uuid4()),
                "term_id": str(uuid.uuid4()),
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
