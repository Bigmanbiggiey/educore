from rest_framework.routers import DefaultRouter

from apps.parents.views import ParentProfileViewSet

app_name = "parents"

router = DefaultRouter()
router.register("parents", ParentProfileViewSet, basename="parent-profile")

urlpatterns = router.urls
