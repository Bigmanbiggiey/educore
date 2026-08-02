from django.contrib import admin

from apps.hostel.models import BedAllocation, Hostel, Room


@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("hostel", "room_number", "capacity")


@admin.register(BedAllocation)
class BedAllocationAdmin(admin.ModelAdmin):
    list_display = ("room", "student_id", "term_id")
