from django.contrib import admin

from apps.classes_streams.models import (
    AcademicYear,
    ClassGrade,
    ClassTeacherAssignment,
    Stream,
    Term,
)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("year_label", "institution_id", "start_date", "end_date")
    search_fields = ("year_label",)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("name", "academic_year", "start_date", "end_date", "is_current")
    list_filter = ("is_current",)


@admin.register(ClassGrade)
class ClassGradeAdmin(admin.ModelAdmin):
    list_display = ("name", "term", "curriculum_type")
    list_filter = ("curriculum_type",)


@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ("name", "class_grade", "capacity")


@admin.register(ClassTeacherAssignment)
class ClassTeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ("class_grade", "stream", "term", "staff_id")
