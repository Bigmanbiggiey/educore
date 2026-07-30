import uuid
from decimal import Decimal

from django.test import TestCase

from apps.core.context import bind_institution
from apps.curriculum_tvet.models import PracticalAssessment
from apps.curriculum_tvet.services import (
    create_competency_unit,
    create_course,
    create_department,
    create_industrial_attachment,
    issue_certificate,
    record_practical_assessment,
)
from apps.institutions.models import Institution


class CurriculumTvetServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def _department(self):
        return create_department(institution=self.institution, name="Engineering")

    def _course(self):
        return create_course(
            institution=self.institution,
            department=self._department(),
            course_code="ENG101",
            name="Automotive Engineering",
        )

    def _competency_unit(self):
        return create_competency_unit(
            institution=self.institution,
            course=self._course(),
            unit_code="CU101",
            name="Engine Repair",
            credit_hours=10,
        )


class CreateReferenceDataTests(CurriculumTvetServiceTestCase):
    def test_create_department_scopes_to_institution(self):
        department = self._department()
        self.assertEqual(department.institution_id, self.institution.id)

    def test_create_course_scopes_to_institution(self):
        course = self._course()
        self.assertEqual(course.institution_id, self.institution.id)

    def test_create_competency_unit_scopes_to_institution(self):
        unit = self._competency_unit()
        self.assertEqual(unit.institution_id, self.institution.id)


class CreateIndustrialAttachmentTests(CurriculumTvetServiceTestCase):
    def test_creates_and_scopes_to_institution(self):
        attachment = create_industrial_attachment(
            institution=self.institution,
            student_id=uuid.uuid4(),
            host_organization="Acme Motors",
            start_date="2026-01-01",
            end_date="2026-03-01",
        )
        self.assertEqual(attachment.institution_id, self.institution.id)

    def test_rejects_a_start_date_after_the_end_date(self):
        with self.assertRaises(ValueError):
            create_industrial_attachment(
                institution=self.institution,
                student_id=uuid.uuid4(),
                host_organization="Acme Motors",
                start_date="2026-06-01",
                end_date="2026-01-01",
            )


class IssueCertificateTests(CurriculumTvetServiceTestCase):
    def test_creates_and_scopes_to_institution(self):
        certificate = issue_certificate(
            institution=self.institution,
            student_id=uuid.uuid4(),
            course=self._course(),
            certificate_number="CERT-001",
        )
        self.assertEqual(certificate.institution_id, self.institution.id)
        self.assertIsNotNone(certificate.issued_at)


class RecordPracticalAssessmentTests(CurriculumTvetServiceTestCase):
    def test_creates_a_new_assessment(self):
        competency_unit = self._competency_unit()
        assessment = record_practical_assessment(
            institution=self.institution,
            student_id=uuid.uuid4(),
            term_id=uuid.uuid4(),
            details={
                "competency_unit_id": str(competency_unit.id),
                "assessment_type": "workshop",
                "score": 65,
                "max_score": 100,
                "assessor_id": str(uuid.uuid4()),
            },
        )
        self.assertEqual(assessment.score, Decimal("65"))

    def test_re_recording_the_same_assessment_type_updates_in_place(self):
        competency_unit = self._competency_unit()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        details = {
            "competency_unit_id": str(competency_unit.id),
            "assessment_type": "workshop",
            "score": 40,
            "max_score": 100,
            "assessor_id": str(uuid.uuid4()),
        }

        record_practical_assessment(
            institution=self.institution, student_id=student_id, term_id=term_id, details=details
        )
        details["score"] = 90
        record_practical_assessment(
            institution=self.institution, student_id=student_id, term_id=term_id, details=details
        )

        with bind_institution(self.institution):
            self.assertEqual(PracticalAssessment.objects.count(), 1)
            self.assertEqual(PracticalAssessment.objects.first().score, Decimal("90"))

    def test_rejects_details_missing_required_keys(self):
        with self.assertRaises(ValueError):
            record_practical_assessment(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={"assessment_type": "workshop"},
            )

    def test_rejects_an_unknown_assessment_type(self):
        competency_unit = self._competency_unit()
        with self.assertRaises(ValueError):
            record_practical_assessment(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={
                    "competency_unit_id": str(competency_unit.id),
                    "assessment_type": "klingon",
                    "score": 1,
                    "max_score": 10,
                    "assessor_id": str(uuid.uuid4()),
                },
            )

    def test_rejects_a_score_above_max_score(self):
        competency_unit = self._competency_unit()
        with self.assertRaises(ValueError):
            record_practical_assessment(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={
                    "competency_unit_id": str(competency_unit.id),
                    "assessment_type": "workshop",
                    "score": 120,
                    "max_score": 100,
                    "assessor_id": str(uuid.uuid4()),
                },
            )

    def test_rejects_a_competency_unit_id_that_does_not_exist(self):
        with self.assertRaises(ValueError):
            record_practical_assessment(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={
                    "competency_unit_id": str(uuid.uuid4()),
                    "assessment_type": "workshop",
                    "score": 1,
                    "max_score": 10,
                    "assessor_id": str(uuid.uuid4()),
                },
            )
