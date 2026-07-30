import uuid

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.core.context import bind_institution
from apps.curriculum_university.models import (
    Dissertation,
    Faculty,
    Graduation,
    Programme,
    School,
    Semester,
    UniversityDepartment,
)
from apps.institutions.models import Domain, Institution
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)

HOSTNAME = "st-mary.educore.africa"


class CurriculumUniversityAPITestCase(APITestCase):
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


class FacultyViewSetTests(CurriculumUniversityAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_university:faculty-list")

    def test_any_active_member_can_list(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 200)

    def test_create_without_permission_is_denied(self):
        response = self.client.post(self.url, {"name": "Science"}, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_university.faculty.manage")

        response = self.client.post(self.url, {"name": "Science"}, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(Faculty.objects.count(), 1)


class HierarchyViewSetTests(CurriculumUniversityAPITestCase):
    """Covers School -> UniversityDepartment -> Programme, one level per
    test, building on the previous level's created row."""

    def setUp(self):
        super().setUp()
        with bind_institution(self.institution):
            self.faculty = Faculty.objects.create(
                institution_id=self.institution.id, name="Science"
            )

    def test_create_school_with_permission_succeeds(self):
        self._grant("curriculum_university.school.manage")
        url = reverse("v1:curriculum_university:school-list")

        response = self.client.post(
            url, {"faculty": str(self.faculty.id), "name": "Computing"}, HTTP_HOST=HOSTNAME
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(School.objects.count(), 1)

    def test_create_department_with_permission_succeeds(self):
        self._grant("curriculum_university.department.manage")
        with bind_institution(self.institution):
            school = School.objects.create(
                institution_id=self.institution.id, faculty=self.faculty, name="Computing"
            )
        url = reverse("v1:curriculum_university:department-list")

        response = self.client.post(
            url,
            {"school": str(school.id), "name": "Software Engineering"},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(UniversityDepartment.objects.count(), 1)

    def test_create_programme_with_permission_succeeds(self):
        self._grant("curriculum_university.programme.manage")
        with bind_institution(self.institution):
            school = School.objects.create(
                institution_id=self.institution.id, faculty=self.faculty, name="Computing"
            )
            department = UniversityDepartment.objects.create(
                institution_id=self.institution.id, school=school, name="Software Engineering"
            )
        url = reverse("v1:curriculum_university:programme-list")

        response = self.client.post(
            url,
            {
                "department": str(department.id),
                "programme_code": "BSC-SE",
                "degree_level": "bachelors",
                "name": "BSc Software Engineering",
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(Programme.objects.count(), 1)


class SemesterViewSetTests(CurriculumUniversityAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_university:semester-list")

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_university.semester.manage")

        response = self.client.post(
            self.url,
            {"term_id": str(uuid.uuid4()), "number": 1, "name": "Semester 1"},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(Semester.objects.count(), 1)


class DissertationViewSetTests(CurriculumUniversityAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_university:dissertation-list")

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_university.dissertation.manage")

        response = self.client.post(
            self.url,
            {
                "student_id": str(uuid.uuid4()),
                "supervisor_id": str(uuid.uuid4()),
                "title": "Machine Learning in Agriculture",
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(Dissertation.objects.count(), 1)


class GraduationViewSetTests(CurriculumUniversityAPITestCase):
    def setUp(self):
        super().setUp()
        with bind_institution(self.institution):
            faculty = Faculty.objects.create(institution_id=self.institution.id, name="Science")
            school = School.objects.create(
                institution_id=self.institution.id, faculty=faculty, name="Computing"
            )
            department = UniversityDepartment.objects.create(
                institution_id=self.institution.id, school=school, name="Software Engineering"
            )
            self.programme = Programme.objects.create(
                institution_id=self.institution.id,
                department=department,
                programme_code="BSC-SE",
                degree_level=Programme.DegreeLevel.BACHELORS,
                name="BSc Software Engineering",
            )
        self.url = reverse("v1:curriculum_university:graduation-list")

    def test_create_with_permission_succeeds(self):
        self._grant("curriculum_university.graduation.manage")

        response = self.client.post(
            self.url,
            {
                "student_id": str(uuid.uuid4()),
                "programme": str(self.programme.id),
                "conferred_at": "2026-06-01T00:00:00Z",
                "classification": "First Class Honours",
            },
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        with bind_institution(self.institution):
            self.assertEqual(Graduation.objects.count(), 1)


class RecomputeGpaViewTests(CurriculumUniversityAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:curriculum_university:recompute-gpa")
        with bind_institution(self.institution):
            self.semester = Semester.objects.create(
                institution_id=self.institution.id,
                term_id=uuid.uuid4(),
                number=1,
                name="Semester 1",
            )

    def test_denied_without_permission(self):
        response = self.client.post(
            self.url, {"semester_id": str(self.semester.id)}, HTTP_HOST=HOSTNAME
        )
        self.assertEqual(response.status_code, 403)

    def test_enqueues_with_permission(self):
        self._grant("curriculum_university.gpa.recompute")

        response = self.client.post(
            self.url, {"semester_id": str(self.semester.id)}, HTTP_HOST=HOSTNAME
        )

        self.assertEqual(response.status_code, 202)
