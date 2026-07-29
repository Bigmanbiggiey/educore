import uuid

from django.test import TestCase

from apps.core.context import bind_institution
from apps.curriculum_cbc.models import Competency, ContinuousAssessment, LearningArea
from apps.curriculum_cbc.services import (
    create_competency,
    create_core_value,
    create_learning_area,
    create_pci,
    record_assessment,
)
from apps.institutions.models import Institution


class CurriculumCbcServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def _learning_area(self):
        return create_learning_area(
            institution=self.institution,
            subject_catalog_id=uuid.uuid4(),
            name="Environmental Activities",
            code="ENV",
        )

    def _competency(self):
        return create_competency(
            institution=self.institution, learning_area=self._learning_area(), strand="Weather"
        )


class CreateReferenceDataTests(CurriculumCbcServiceTestCase):
    def test_create_learning_area_scopes_to_institution(self):
        learning_area = self._learning_area()
        self.assertEqual(learning_area.institution_id, self.institution.id)
        self.assertIsInstance(learning_area, LearningArea)

    def test_create_competency_scopes_to_institution(self):
        competency = self._competency()
        self.assertEqual(competency.institution_id, self.institution.id)
        self.assertIsInstance(competency, Competency)

    def test_create_core_value_scopes_to_institution(self):
        core_value = create_core_value(institution=self.institution, name="Respect")
        self.assertEqual(core_value.institution_id, self.institution.id)

    def test_create_pci_scopes_to_institution(self):
        pci = create_pci(institution=self.institution, name="Environmental degradation")
        self.assertEqual(pci.institution_id, self.institution.id)


class RecordAssessmentTests(CurriculumCbcServiceTestCase):
    def test_creates_a_new_assessment(self):
        competency = self._competency()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()

        assessment = record_assessment(
            institution=self.institution,
            student_id=student_id,
            term_id=term_id,
            details={
                "competency_id": str(competency.id),
                "performance_level": "meeting_expectation",
                "evidence_notes": "Good work",
            },
        )

        self.assertEqual(assessment.performance_level, "meeting_expectation")
        with bind_institution(self.institution):
            self.assertEqual(ContinuousAssessment.objects.count(), 1)

    def test_reassessing_the_same_student_competency_term_updates_in_place(self):
        competency = self._competency()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()

        record_assessment(
            institution=self.institution,
            student_id=student_id,
            term_id=term_id,
            details={"competency_id": str(competency.id), "performance_level": "below_expectation"},
        )
        record_assessment(
            institution=self.institution,
            student_id=student_id,
            term_id=term_id,
            details={
                "competency_id": str(competency.id),
                "performance_level": "exceeding_expectation",
            },
        )

        with bind_institution(self.institution):
            self.assertEqual(ContinuousAssessment.objects.count(), 1)
            self.assertEqual(
                ContinuousAssessment.objects.first().performance_level, "exceeding_expectation"
            )

    def test_rejects_details_missing_required_keys(self):
        with self.assertRaises(ValueError):
            record_assessment(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={"performance_level": "meeting_expectation"},
            )

    def test_rejects_an_unknown_performance_level(self):
        competency = self._competency()
        with self.assertRaises(ValueError):
            record_assessment(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={"competency_id": str(competency.id), "performance_level": "klingon"},
            )

    def test_rejects_a_competency_id_that_does_not_exist(self):
        with self.assertRaises(ValueError):
            record_assessment(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={
                    "competency_id": str(uuid.uuid4()),
                    "performance_level": "meeting_expectation",
                },
            )

    def test_rejects_a_malformed_competency_id(self):
        with self.assertRaises(ValueError):
            record_assessment(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={"competency_id": "not-a-uuid", "performance_level": "meeting_expectation"},
            )
