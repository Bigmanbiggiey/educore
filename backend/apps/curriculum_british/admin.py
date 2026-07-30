from django.contrib import admin

from apps.curriculum_british.models import Coursework, PredictedGrade, Subject, YearGroup


@admin.register(YearGroup)
class YearGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "key_stage", "order", "institution_id")
    list_filter = ("key_stage",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "qualification_level", "institution_id")
    list_filter = ("qualification_level",)


@admin.register(Coursework)
class CourseworkAdmin(admin.ModelAdmin):
    list_display = ("subject", "student_id", "term_id", "component", "score", "max_score")


@admin.register(PredictedGrade)
class PredictedGradeAdmin(admin.ModelAdmin):
    list_display = ("subject", "student_id", "academic_year_id", "predicted_grade")
