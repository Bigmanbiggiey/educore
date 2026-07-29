from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.academics import registry
from apps.academics.contracts import AssessmentEngine, ReportEngine
from apps.accounts.models import User
from apps.classes_streams.models import AcademicYear, ClassGrade, Term
from apps.core.context import bind_institution
from apps.institutions.models import Domain, Institution, InstitutionCurriculum
from apps.permissions.models import (
    InstitutionMembership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)
from apps.students.models import Enrollment, GuardianRelationship, Student

HOSTNAME = "st-mary.educore.africa"
_CBC = InstitutionCurriculum.CurriculumType.CBC


class _DummyEngine(AssessmentEngine, ReportEngine):
    def record_assessment(self, *, institution, student_id, term_id, details):
        if "explode" in details:
            raise ValueError("bad details")
        return {"recorded": True, "student_id": str(student_id)}

    def compute_result(self, *, institution, student_id, term_id):
        return None

    def generate_report_data(self, *, institution, student_id, term_id):
        return {"student_id": str(student_id), "term_id": str(term_id)}


class AcademicsAPITestCase(APITestCase):
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


class SubjectCatalogViewSetTests(AcademicsAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:academics:subject-list")

    def test_any_active_member_can_list(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 200)

    def test_create_without_permission_is_denied(self):
        response = self.client.post(
            self.url,
            {"curriculum_type": "cbc", "name": "Mathematics", "code": "MATH"},
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_create_with_permission_succeeds(self):
        self._grant("academics.subject_catalog.manage")

        response = self.client.post(
            self.url,
            {"curriculum_type": "cbc", "name": "Mathematics", "code": "MATH"},
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)


class GradingScaleViewSetTests(AcademicsAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:academics:grading-scale-list")

    def test_create_with_permission_succeeds(self):
        self._grant("academics.grading_scale.manage")

        response = self.client.post(
            self.url,
            {"curriculum_type": "cbc", "levels": [{"label": "EE", "min": 80, "max": 100}]},
            format="json",
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)


class CurriculumAgnosticAPITestCase(AcademicsAPITestCase):
    """Base for `AssessmentRecordView`/`ReportCardView` tests — registers a
    throwaway engine for the duration of the test, and builds a real
    Student enrolled in a CBC `ClassGrade` so curriculum resolution has
    something real to chain through."""

    def setUp(self):
        super().setUp()
        self._saved_registry = dict(registry._registry)
        registry._registry.clear()
        registry.register(_CBC, _DummyEngine)
        self.addCleanup(self._restore_registry)

        with bind_institution(self.institution):
            InstitutionCurriculum.objects.create(
                institution=self.institution, curriculum_type=_CBC, is_active=True
            )
            year = AcademicYear.objects.create(
                institution_id=self.institution.id,
                year_label="2026",
                start_date="2026-01-01",
                end_date="2026-12-31",
            )
            self.term = Term.objects.create(
                institution_id=self.institution.id,
                academic_year=year,
                name="Term 1",
                start_date="2026-01-01",
                end_date="2026-04-01",
            )
            class_grade = ClassGrade.objects.create(
                institution_id=self.institution.id,
                term=self.term,
                name="Grade 4",
                curriculum_type=_CBC,
            )
            self.student = Student.objects.create(
                institution_id=self.institution.id,
                admission_number="ADM-1",
                first_name="Amina",
                last_name="Otieno",
            )
            Enrollment.objects.create(
                institution_id=self.institution.id,
                student=self.student,
                class_grade_id=class_grade.id,
                term_id=self.term.id,
            )

    def _restore_registry(self):
        registry._registry.clear()
        registry._registry.update(self._saved_registry)


class AssessmentRecordViewTests(CurriculumAgnosticAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("v1:academics:assessment-record")

    def test_denied_without_permission(self):
        response = self.client.post(
            self.url,
            {"student_id": str(self.student.id), "term_id": str(self.term.id), "details": {}},
            format="json",
            HTTP_HOST=HOSTNAME,
        )
        self.assertEqual(response.status_code, 403)

    def test_resolves_through_the_registered_engine_with_permission(self):
        self._grant("academics.assessment.record")

        response = self.client.post(
            self.url,
            {"student_id": str(self.student.id), "term_id": str(self.term.id), "details": {}},
            format="json",
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["student_id"], str(self.student.id))

    def test_a_value_error_from_the_engine_becomes_a_400(self):
        self._grant("academics.assessment.record")

        response = self.client.post(
            self.url,
            {
                "student_id": str(self.student.id),
                "term_id": str(self.term.id),
                "details": {"explode": True},
            },
            format="json",
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 400)

    def test_a_student_with_no_active_enrollment_is_a_404(self):
        self._grant("academics.assessment.record")
        with bind_institution(self.institution):
            other_student = Student.objects.create(
                institution_id=self.institution.id,
                admission_number="ADM-2",
                first_name="No",
                last_name="Enrollment",
            )

        response = self.client.post(
            self.url,
            {"student_id": str(other_student.id), "term_id": str(self.term.id), "details": {}},
            format="json",
            HTTP_HOST=HOSTNAME,
        )

        self.assertEqual(response.status_code, 404)


class ReportCardViewTests(CurriculumAgnosticAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "v1:academics:report-card",
            kwargs={"student_id": self.student.id, "term_id": self.term.id},
        )

    def test_any_active_member_can_pull_a_report(self):
        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["student_id"], str(self.student.id))

    def test_a_parent_of_a_different_student_is_denied(self):
        role = Role.objects.create(name="Parent", institution=self.institution)
        MembershipRole.objects.create(membership=self.membership, role=role)

        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 403)

    def test_the_students_own_guardian_is_allowed(self):
        role = Role.objects.create(name="Parent", institution=self.institution)
        MembershipRole.objects.create(membership=self.membership, role=role)
        with bind_institution(self.institution):
            GuardianRelationship.objects.create(
                institution_id=self.institution.id,
                student=self.student,
                guardian_user_id=self.user.id,
                relationship_type=GuardianRelationship.RelationshipType.PARENT,
            )

        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)

    def test_a_different_student_is_denied(self):
        role = Role.objects.create(name="Student", institution=self.institution)
        MembershipRole.objects.create(membership=self.membership, role=role)

        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 403)

    def test_the_students_own_account_is_allowed(self):
        role = Role.objects.create(name="Student", institution=self.institution)
        MembershipRole.objects.create(membership=self.membership, role=role)
        with bind_institution(self.institution):
            self.student.user_id = self.user.id
            self.student.save(update_fields=["user_id"])

        response = self.client.get(self.url, HTTP_HOST=HOSTNAME)

        self.assertEqual(response.status_code, 200)
