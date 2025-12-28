from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api import views
from organizations.views import AssociationViewSet, TeamViewSet
from tryouts.views import TryoutEventViewSet

router = DefaultRouter()
router.register(r"associations", AssociationViewSet, basename="association")
router.register(r"teams", TeamViewSet, basename="team")
router.register(r"tryouts", TryoutEventViewSet, basename="tryout")

urlpatterns = [
    path("health/", views.health, name="health"),
    path("me/", views.me, name="me"),
    path("protected/", views.protected, name="protected"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include(router.urls)),
]
