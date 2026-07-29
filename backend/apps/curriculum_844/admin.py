from django.contrib import admin

from apps.curriculum_844.models import ExamResult, MeanGradeSnapshot, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "institution_id")


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ("subject", "student_id", "term_id", "exam_type", "score", "max_score")
    list_filter = ("exam_type",)


@admin.register(MeanGradeSnapshot)
class MeanGradeSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "student_id",
        "term_id",
        "mean_score",
        "mean_grade",
        "rank_in_class",
        "rank_in_stream",
    )
