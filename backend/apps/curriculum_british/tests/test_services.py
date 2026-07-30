import uuid
from decimal import Decimal

from django.test import TestCase

from apps.core.context import bind_institution
from apps.curriculum_british.models import Coursework, PredictedGrade, YearGroup
from apps.curriculum_british.services import (
    create_subject,
    create_year_group,
    record_coursework,
    set_predicted_grade,
)
from apps.institutions.models import Institution


class CurriculumBritishServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def _subject(self, code="MATH"):
        return create_subject(
            institution=self.institution,
            subject_catalog_id=uuid.uuid4(),
            name="Mathematics",
            code=code,
        )


class CreateYearGroupTests(CurriculumBritishServiceTestCase):
    def test_creates_and_scopes_to_institution(self):
        year_group = create_year_group(
            institution=self.institution,
            class_grade_id=uuid.uuid4(),
            key_stage="ks3",
            name="Year 7",
            order=7,
        )
        self.assertEqual(year_group.institution_id, self.institution.id)
        self.assertIsInstance(year_group, YearGroup)

    def test_rejects_an_unknown_key_stage(self):
        with self.assertRaises(ValueError):
            create_year_group(
                institution=self.institution,
                class_grade_id=uuid.uuid4(),
                key_stage="klingon",
                name="Year 7",
                order=7,
            )


class RecordCourseworkTests(CurriculumBritishServiceTestCase):
    def test_creates_a_new_coursework_entry(self):
        subject = self._subject()
        coursework = record_coursework(
            institution=self.institution,
            student_id=uuid.uuid4(),
            term_id=uuid.uuid4(),
            details={
                "subject_id": str(subject.id),
                "component": "Unit 1",
                "score": 65,
                "max_score": 100,
            },
        )
        self.assertEqual(coursework.score, Decimal("65"))

    def test_re_recording_the_same_component_updates_in_place(self):
        subject = self._subject()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        details = {
            "subject_id": str(subject.id),
            "component": "Unit 1",
            "score": 40,
            "max_score": 100,
        }

        record_coursework(
            institution=self.institution, student_id=student_id, term_id=term_id, details=details
        )
        details["score"] = 90
        record_coursework(
            institution=self.institution, student_id=student_id, term_id=term_id, details=details
        )

        with bind_institution(self.institution):
            self.assertEqual(Coursework.objects.count(), 1)
            self.assertEqual(Coursework.objects.first().score, Decimal("90"))

    def test_rejects_details_missing_required_keys(self):
        with self.assertRaises(ValueError):
            record_coursework(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={"component": "Unit 1"},
            )

    def test_rejects_a_score_above_max_score(self):
        subject = self._subject()
        with self.assertRaises(ValueError):
            record_coursework(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={
                    "subject_id": str(subject.id),
                    "component": "Unit 1",
                    "score": 120,
                    "max_score": 100,
                },
            )

    def test_rejects_a_subject_id_that_does_not_exist(self):
        with self.assertRaises(ValueError):
            record_coursework(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={
                    "subject_id": str(uuid.uuid4()),
                    "component": "Unit 1",
                    "score": 1,
                    "max_score": 10,
                },
            )


class SetPredictedGradeTests(CurriculumBritishServiceTestCase):
    def test_creates_a_new_predicted_grade(self):
        subject = self._subject()
        grade = set_predicted_grade(
            institution=self.institution,
            student_id=uuid.uuid4(),
            subject=subject,
            academic_year_id=uuid.uuid4(),
            predicted_grade="A*",
            set_by=uuid.uuid4(),
        )
        self.assertEqual(grade.predicted_grade, "A*")

    def test_setting_it_again_updates_in_place(self):
        subject = self._subject()
        student_id = uuid.uuid4()
        academic_year_id = uuid.uuid4()
        first_teacher = uuid.uuid4()
        second_teacher = uuid.uuid4()

        set_predicted_grade(
            institution=self.institution,
            student_id=student_id,
            subject=subject,
            academic_year_id=academic_year_id,
            predicted_grade="B",
            set_by=first_teacher,
        )
        set_predicted_grade(
            institution=self.institution,
            student_id=student_id,
            subject=subject,
            academic_year_id=academic_year_id,
            predicted_grade="A",
            set_by=second_teacher,
        )

        with bind_institution(self.institution):
            self.assertEqual(PredictedGrade.objects.count(), 1)
            updated = PredictedGrade.objects.first()
            self.assertEqual(updated.predicted_grade, "A")
            self.assertEqual(updated.set_by, second_teacher)
