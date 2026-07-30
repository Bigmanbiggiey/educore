from django.contrib import admin

from apps.curriculum_tvet.models import (
    Certificate,
    CompetencyUnit,
    Course,
    IndustrialAttachment,
    PracticalAssessment,
    TVETDepartment,
)


@admin.register(TVETDepartment)
class TVETDepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "institution_id")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "course_code", "department")


@admin.register(CompetencyUnit)
class CompetencyUnitAdmin(admin.ModelAdmin):
    list_display = ("name", "unit_code", "course", "credit_hours")


@admin.register(IndustrialAttachment)
class IndustrialAttachmentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "host_organization", "start_date", "end_date")


@admin.register(PracticalAssessment)
class PracticalAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "competency_unit",
        "student_id",
        "term_id",
        "assessment_type",
        "score",
        "max_score",
    )
    list_filter = ("assessment_type",)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_number", "student_id", "course", "issued_at")
