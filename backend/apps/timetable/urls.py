from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.timetable.views import PeriodViewSet, SubjectSlotAssignmentViewSet, TimetableViewSet

app_name = "timetable"

router = DefaultRouter()
router.register("timetables", TimetableViewSet, basename="timetable")
router.register(
    "subject-slot-assignments", SubjectSlotAssignmentViewSet, basename="subject-slot-assignment"
)

_period_list = PeriodViewSet.as_view({"get": "list", "post": "create"})
_period_detail = PeriodViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    *router.urls,
    path("timetables/<uuid:timetable_pk>/periods/", _period_list, name="timetable-periods-list"),
    path(
        "timetables/<uuid:timetable_pk>/periods/<uuid:pk>/",
        _period_detail,
        name="timetable-periods-detail",
    ),
]
