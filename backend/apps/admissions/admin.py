from django.contrib import admin

from apps.admissions.models import Application, ApplicationStage, Offer


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "institution_id", "stage", "term_applying_for_id")
    list_filter = ("stage",)


@admin.register(ApplicationStage)
class ApplicationStageAdmin(admin.ModelAdmin):
    list_display = ("application", "stage", "created_at")
    list_filter = ("stage",)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("application", "offered_at", "accepted_at")
