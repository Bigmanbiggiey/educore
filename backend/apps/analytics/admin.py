from django.contrib import admin

from apps.analytics.models import AttendanceRateSnapshot, FeeCollectionSnapshot, MeanGradeRollup


@admin.register(AttendanceRateSnapshot)
class AttendanceRateSnapshotAdmin(admin.ModelAdmin):
    list_display = ("class_grade_id", "term_id", "rate")


@admin.register(FeeCollectionSnapshot)
class FeeCollectionSnapshotAdmin(admin.ModelAdmin):
    list_display = ("class_grade_id", "term_id", "collection_rate")


@admin.register(MeanGradeRollup)
class MeanGradeRollupAdmin(admin.ModelAdmin):
    list_display = ("class_grade_id", "term_id", "mean_grade")
