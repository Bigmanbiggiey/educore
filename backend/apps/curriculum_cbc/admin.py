from django.contrib import admin

from apps.curriculum_cbc.models import (
    PCI,
    Competency,
    ContinuousAssessment,
    CoreValue,
    LearningArea,
    Project,
)


@admin.register(LearningArea)
class LearningAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "institution_id")


@admin.register(Competency)
class CompetencyAdmin(admin.ModelAdmin):
    list_display = ("learning_area", "strand", "sub_strand")


@admin.register(CoreValue)
class CoreValueAdmin(admin.ModelAdmin):
    list_display = ("name", "institution_id")


@admin.register(PCI)
class PCIAdmin(admin.ModelAdmin):
    list_display = ("name", "institution_id")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("competency", "student_id", "term_id")


@admin.register(ContinuousAssessment)
class ContinuousAssessmentAdmin(admin.ModelAdmin):
    list_display = ("competency", "student_id", "term_id", "performance_level")
    list_filter = ("performance_level",)
