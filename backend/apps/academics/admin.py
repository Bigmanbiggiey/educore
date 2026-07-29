from django.contrib import admin

from apps.academics.models import GradingScale, SubjectCatalog


@admin.register(GradingScale)
class GradingScaleAdmin(admin.ModelAdmin):
    list_display = ("curriculum_type", "institution_id")
    list_filter = ("curriculum_type",)


@admin.register(SubjectCatalog)
class SubjectCatalogAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "curriculum_type")
    list_filter = ("curriculum_type",)
    search_fields = ("name", "code")
