import datetime
import decimal
import uuid

from django.test import TestCase

from apps.analytics.models import AttendanceRateSnapshot
from apps.classes_streams.services import create_academic_year, create_class_grade, create_term
from apps.core.context import bind_institution
from apps.dashboard.selectors import (
    get_parent_dashboard,
    get_principal_dashboard,
    get_student_dashboard,
    get_teacher_dashboard,
)
from apps.institutions.services import provision_institution
from apps.staff.services import create_staff_profile
from apps.students.services import add_guardian, create_student, enroll_student
from apps.timetable.services import assign_slot, create_period, create_timetable


class DashboardSelectorTestCase(TestCase):
    def setUp(self):
        self.institution = provision_institution(
            name="St Mary", slug=f"st-mary-dash-{uuid.uuid4().hex[:8]}", curriculum_types=["cbc"]
        )
        academic_year = create_academic_year(
            institution=self.institution,
            year_label="2026",
            start_date="2026-01-01",
            end_date="2026-12-01",
        )
        self.term = create_term(
            institution=self.institution,
            academic_year=academic_year,
            name="Term 1",
            start_date="2026-01-01",
            end_date="2026-04-01",
        )
        self.class_grade = create_class_grade(
            institution=self.institution, term=self.term, name="Form 1", curriculum_type="cbc"
        )


class GetPrincipalDashboardTests(DashboardSelectorTestCase):
    def test_reflects_the_institutions_rollups(self):
        with bind_institution(self.institution):
            AttendanceRateSnapshot.objects.create(
                institution_id=self.institution.id,
                class_grade_id=self.class_grade.id,
                term_id=self.term.id,
                rate=decimal.Decimal("0.8"),
            )

        data = get_principal_dashboard(self.institution, self.term.id)

        self.assertEqual(data["average_attendance_rate"], decimal.Decimal("0.8"))


class GetTeacherDashboardTests(DashboardSelectorTestCase):
    def test_returns_the_teachers_own_schedule(self):
        staff = create_staff_profile(
            institution=self.institution,
            user_id=uuid.uuid4(),
            employee_number="T-001",
            first_name="Ann",
            last_name="Teacher",
            employment_type="full_time",
        )
        timetable = create_timetable(
            institution=self.institution, term_id=self.term.id, class_grade_id=self.class_grade.id
        )
        period = create_period(
            institution=self.institution,
            timetable=timetable,
            day_of_week=0,
            start_time=datetime.time(8, 0),
            end_time=datetime.time(9, 0),
        )
        assign_slot(
            institution=self.institution,
            period=period,
            subject_id=uuid.uuid4(),
            staff_id=staff.id,
            room="Lab 1",
        )

        data = get_teacher_dashboard(self.institution, staff.id)

        self.assertEqual(len(data["schedule"]), 1)
        self.assertEqual(data["schedule"][0]["room"], "Lab 1")


class GetParentDashboardTests(DashboardSelectorTestCase):
    def test_returns_each_childs_balance(self):
        student = create_student(
            institution=self.institution,
            admission_number="A-001",
            first_name="Kid",
            last_name="One",
        )
        enroll_student(
            institution=self.institution,
            student=student,
            class_grade_id=self.class_grade.id,
            term_id=self.term.id,
        )
        guardian_user_id = uuid.uuid4()
        add_guardian(
            institution=self.institution,
            student=student,
            guardian_user_id=guardian_user_id,
            relationship_type="parent",
        )

        data = get_parent_dashboard(self.institution, guardian_user_id, self.term.id)

        self.assertEqual(len(data["children"]), 1)
        self.assertEqual(data["children"][0]["student_id"], student.id)


class GetStudentDashboardTests(DashboardSelectorTestCase):
    def test_returns_the_students_own_attendance_and_balance(self):
        student = create_student(
            institution=self.institution,
            admission_number="A-002",
            first_name="Kid",
            last_name="Two",
        )
        enroll_student(
            institution=self.institution,
            student=student,
            class_grade_id=self.class_grade.id,
            term_id=self.term.id,
        )

        data = get_student_dashboard(self.institution, student, self.term.id)

        self.assertIsNone(data["attendance_rate"])
        self.assertEqual(data["balance"], decimal.Decimal("0"))
        self.assertEqual(data["documents"], [])
