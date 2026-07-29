import uuid
from decimal import Decimal

from django.test import TestCase

from apps.core.context import bind_institution
from apps.curriculum_844.models import ExamResult, MeanGradeSnapshot, Subject
from apps.curriculum_844.services import (
    create_subject,
    import_kcpe_kcse_results,
    recompute_mean_grade_snapshots,
    record_exam_result,
)
from apps.institutions.models import Institution
from apps.students.models import Enrollment, Student


class Curriculum844ServiceTestCase(TestCase):
    def setUp(self):
        self.institution = Institution.objects.create(name="St Mary", slug="st-mary")

    def _subject(self, code="MATH"):
        return create_subject(
            institution=self.institution,
            subject_catalog_id=uuid.uuid4(),
            name="Mathematics",
            code=code,
        )


class CreateSubjectTests(Curriculum844ServiceTestCase):
    def test_scopes_to_institution(self):
        subject = self._subject()
        self.assertEqual(subject.institution_id, self.institution.id)
        self.assertIsInstance(subject, Subject)


class RecordExamResultTests(Curriculum844ServiceTestCase):
    def test_creates_a_new_result(self):
        subject = self._subject()
        result = record_exam_result(
            institution=self.institution,
            student_id=uuid.uuid4(),
            term_id=uuid.uuid4(),
            details={
                "subject_id": str(subject.id),
                "exam_type": "cat",
                "score": 65,
                "max_score": 100,
            },
        )
        self.assertEqual(result.score, Decimal("65"))

    def test_re_recording_the_same_result_updates_in_place(self):
        subject = self._subject()
        student_id = uuid.uuid4()
        term_id = uuid.uuid4()
        details = {"subject_id": str(subject.id), "exam_type": "cat", "score": 40, "max_score": 100}

        record_exam_result(
            institution=self.institution, student_id=student_id, term_id=term_id, details=details
        )
        details["score"] = 90
        record_exam_result(
            institution=self.institution, student_id=student_id, term_id=term_id, details=details
        )

        with bind_institution(self.institution):
            self.assertEqual(ExamResult.objects.count(), 1)
            self.assertEqual(ExamResult.objects.first().score, Decimal("90"))

    def test_rejects_details_missing_required_keys(self):
        with self.assertRaises(ValueError):
            record_exam_result(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={"exam_type": "cat"},
            )

    def test_rejects_an_unknown_exam_type(self):
        subject = self._subject()
        with self.assertRaises(ValueError):
            record_exam_result(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={
                    "subject_id": str(subject.id),
                    "exam_type": "klingon",
                    "score": 1,
                    "max_score": 10,
                },
            )

    def test_rejects_a_score_above_max_score(self):
        subject = self._subject()
        with self.assertRaises(ValueError):
            record_exam_result(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={
                    "subject_id": str(subject.id),
                    "exam_type": "cat",
                    "score": 120,
                    "max_score": 100,
                },
            )

    def test_rejects_a_subject_id_that_does_not_exist(self):
        with self.assertRaises(ValueError):
            record_exam_result(
                institution=self.institution,
                student_id=uuid.uuid4(),
                term_id=uuid.uuid4(),
                details={
                    "subject_id": str(uuid.uuid4()),
                    "exam_type": "cat",
                    "score": 1,
                    "max_score": 10,
                },
            )


class ImportKcpeKcseResultsTests(Curriculum844ServiceTestCase):
    def test_creates_results_tagged_as_kcpe_kcse(self):
        subject = self._subject()
        term_id = uuid.uuid4()

        results = import_kcpe_kcse_results(
            institution=self.institution,
            term_id=term_id,
            rows=[
                {
                    "student_id": uuid.uuid4(),
                    "subject_id": subject.id,
                    "score": 78,
                    "max_score": 100,
                },
            ],
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].exam_type, "kcpe_kcse")

    def test_the_whole_batch_rolls_back_on_one_bad_row(self):
        subject = self._subject()
        term_id = uuid.uuid4()

        with self.assertRaises(ValueError):
            import_kcpe_kcse_results(
                institution=self.institution,
                term_id=term_id,
                rows=[
                    {
                        "student_id": uuid.uuid4(),
                        "subject_id": subject.id,
                        "score": 78,
                        "max_score": 100,
                    },
                    {
                        "student_id": uuid.uuid4(),
                        "subject_id": subject.id,
                        "score": 200,
                        "max_score": 100,
                    },
                ],
            )

        with bind_institution(self.institution):
            self.assertEqual(ExamResult.objects.count(), 0)


class RecomputeMeanGradeSnapshotsTests(Curriculum844ServiceTestCase):
    def _enroll(self, class_grade_id, term_id, stream_id, admission_number):
        with bind_institution(self.institution):
            student = Student.objects.create(
                institution_id=self.institution.id,
                admission_number=admission_number,
                first_name="A",
                last_name="B",
            )
            Enrollment.objects.create(
                institution_id=self.institution.id,
                student=student,
                class_grade_id=class_grade_id,
                stream_id=stream_id,
                term_id=term_id,
            )
        return student

    def test_ranks_students_by_mean_score_within_class_and_stream(self):
        subject = self._subject()
        class_grade_id = uuid.uuid4()
        term_id = uuid.uuid4()
        stream_a = uuid.uuid4()
        stream_b = uuid.uuid4()

        top_student = self._enroll(class_grade_id, term_id, stream_a, "ADM-1")
        middle_student = self._enroll(class_grade_id, term_id, stream_a, "ADM-2")
        bottom_student = self._enroll(class_grade_id, term_id, stream_b, "ADM-3")

        for student, score in ((top_student, 90), (middle_student, 60), (bottom_student, 30)):
            record_exam_result(
                institution=self.institution,
                student_id=student.id,
                term_id=term_id,
                details={
                    "subject_id": str(subject.id),
                    "exam_type": "end_term",
                    "score": score,
                    "max_score": 100,
                },
            )

        recompute_mean_grade_snapshots(
            institution=self.institution, term_id=term_id, class_grade_id=class_grade_id
        )

        with bind_institution(self.institution):
            top_snapshot = MeanGradeSnapshot.objects.get(student_id=top_student.id, term_id=term_id)
            middle_snapshot = MeanGradeSnapshot.objects.get(
                student_id=middle_student.id, term_id=term_id
            )
            bottom_snapshot = MeanGradeSnapshot.objects.get(
                student_id=bottom_student.id, term_id=term_id
            )

        self.assertEqual(top_snapshot.rank_in_class, 1)
        self.assertEqual(middle_snapshot.rank_in_class, 2)
        self.assertEqual(bottom_snapshot.rank_in_class, 3)
        # top_student and middle_student are in the same stream (stream_a);
        # bottom_student is alone in stream_b.
        self.assertEqual(top_snapshot.rank_in_stream, 1)
        self.assertEqual(middle_snapshot.rank_in_stream, 2)
        self.assertEqual(bottom_snapshot.rank_in_stream, 1)

    def test_students_with_no_exam_results_are_skipped(self):
        class_grade_id = uuid.uuid4()
        term_id = uuid.uuid4()
        self._enroll(class_grade_id, term_id, uuid.uuid4(), "ADM-1")

        snapshots = recompute_mean_grade_snapshots(
            institution=self.institution, term_id=term_id, class_grade_id=class_grade_id
        )

        self.assertEqual(snapshots, [])
