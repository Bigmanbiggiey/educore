from rest_framework.routers import DefaultRouter

from apps.library.views import (
    BookViewSet,
    CopyViewSet,
    FineViewSet,
    LoanViewSet,
    ReservationViewSet,
)

app_name = "library"

router = DefaultRouter()
router.register("books", BookViewSet, basename="book")
router.register("copies", CopyViewSet, basename="copy")
router.register("loans", LoanViewSet, basename="loan")
router.register("reservations", ReservationViewSet, basename="reservation")
router.register("fines", FineViewSet, basename="fine")

urlpatterns = router.urls
