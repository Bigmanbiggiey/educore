from django.contrib import admin

from apps.transport.models import Route, Stop, TransportAssignment, Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("registration_number", "capacity", "status")
    list_filter = ("status",)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("name", "vehicle")


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ("name", "route", "sequence")


@admin.register(TransportAssignment)
class TransportAssignmentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "route", "stop")
