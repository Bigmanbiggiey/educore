import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.core.context import bind_institution
from apps.curriculum_tvet.models import (
    Certificate,
    CompetencyUnit,
    Course,
    IndustrialAttachment,
    PracticalAssessment,
    TVETDepartment,
)
from apps.institutions.models import Institution


class CurriculumTvetTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")
        self.ctx = bind_institution(self.institution)
        self.ctx.__enter__()
        self.addCleanup(self.ctx.__exit__, None, None, None)

    def _department(self, name="Engineering"):
        return TVETDepartment.objects.create(institution_id=self.institution.id, name=name)

    def _course(self, code="ENG101", department=None):
        return Course.objects.create(
            institution_id=self.institution.id,
            department=department or self._department(),
            course_code=code,
            name="Automotive Engineering",
        )

    def _competency_unit(self, course=None):
        return CompetencyUnit.objects.create(
            institution_id=self.institution.id,
            course=course or self._course(),
            unit_code="CU101",
            name="Engine Repair",
            credit_hours=10,
        )


class TVETDepartmentConstraintTests(CurriculumTvetTestCase):
    def test_unique_name_per_institution(self):
        self._department(name="Engineering")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._department(name="Engineering")


class CourseConstraintTests(CurriculumTvetTestCase):
    def test_unique_code_per_institution(self):
        self._course(code="ENG101")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._course(code="ENG101")


class CompetencyUnitConstraintTests(CurriculumTvetTestCase):
    def test_unique_unit_code_per_course(self):
        course = self._course()
        self._competency_unit(course=course)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._competency_unit(course=course)


class IndustrialAttachmentConstraintTests(CurriculumTvetTestCase):
    def test_start_before_end_is_enforced(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                IndustrialAttachment.objects.create(
                    institution_id=self.institution.id,
                    student_id=uuid.uuid4(),
                    host_organization="Acme Motors",
                    start_date="2026-06-01",
                    end_date="2026-01-01",
                )


class PracticalAssessmentConstraintTests(CurriculumTvetTestCase):
    def test_unique_per_student_unit_term_type(self):
        competency_unit = self._competency_unit()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        PracticalAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            competency_unit=competency_unit,
            term_id=term_id,
            assessment_type=PracticalAssessment.AssessmentType.WORKSHOP,
            score="60.00",
            max_score="100.00",
            assessor_id=uuid.uuid4(),
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PracticalAssessment.objects.create(
                    institution_id=self.institution.id,
                    student_id=student_id,
                    competency_unit=competency_unit,
                    term_id=term_id,
                    assessment_type=PracticalAssessment.AssessmentType.WORKSHOP,
                    score="70.00",
                    max_score="100.00",
                    assessor_id=uuid.uuid4(),
                )

    def test_a_different_assessment_type_is_allowed(self):
        competency_unit = self._competency_unit()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        PracticalAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            competency_unit=competency_unit,
            term_id=term_id,
            assessment_type=PracticalAssessment.AssessmentType.WORKSHOP,
            score="60.00",
            max_score="100.00",
            assessor_id=uuid.uuid4(),
        )
        PracticalAssessment.objects.create(
            institution_id=self.institution.id,
            student_id=student_id,
            competency_unit=competency_unit,
            term_id=term_id,
            assessment_type=PracticalAssessment.AssessmentType.PRACTICAL_EXAM,
            score="70.00",
            max_score="100.00",
            assessor_id=uuid.uuid4(),
        )  # must not raise

    def test_score_cannot_exceed_max_score(self):
        competency_unit = self._competency_unit()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PracticalAssessment.objects.create(
                    institution_id=self.institution.id,
                    student_id=uuid.uuid4(),
                    competency_unit=competency_unit,
                    term_id=uuid.uuid4(),
                    assessment_type=PracticalAssessment.AssessmentType.WORKSHOP,
                    score="101.00",
                    max_score="100.00",
                    assessor_id=uuid.uuid4(),
                )


class CertificateConstraintTests(CurriculumTvetTestCase):
    def test_unique_certificate_number_per_institution(self):
        course = self._course()
        Certificate.objects.create(
            institution_id=self.institution.id,
            student_id=uuid.uuid4(),
            course=course,
            certificate_number="CERT-001",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Certificate.objects.create(
                    institution_id=self.institution.id,
                    student_id=uuid.uuid4(),
                    course=course,
                    certificate_number="CERT-001",
                )

    def test_issued_at_defaults_to_now(self):
        course = self._course()
        certificate = Certificate.objects.create(
            institution_id=self.institution.id,
            student_id=uuid.uuid4(),
            course=course,
            certificate_number="CERT-002",
        )
        self.assertIsNotNone(certificate.issued_at)
