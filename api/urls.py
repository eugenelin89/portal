from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api import views
from availability import views as availability_views
from contacts.views import ContactRequestViewSet, contact_request_respond, open_players
from profiles import views as profile_views
from organizations.views import AssociationViewSet, TeamViewSet
from tryouts.views import TryoutEventViewSet

router = DefaultRouter()
router.register(r"associations", AssociationViewSet, basename="association")
router.register(r"teams", TeamViewSet, basename="team")
router.register(r"tryouts", TryoutEventViewSet, basename="tryout")
router.register(r"contact-requests", ContactRequestViewSet, basename="contact_request")

urlpatterns = [
    path("health/", views.health, name="health"),
    path("me/", views.me, name="me"),
    path("availability/me/", availability_views.availability_me, name="availability_me"),
    path(
        "availability/allowed-associations/",
        availability_views.availability_allowed_associations,
        name="availability_allowed_associations",
    ),
    path(
        "availability/allowed-associations/<int:association_id>/",
        availability_views.availability_allowed_association_delete,
        name="availability_allowed_association_delete",
    ),
    path("availability/search/", availability_views.availability_search, name="availability_search"),
    path("profile/me/", profile_views.profile_me, name="profile_me"),
    path("contact-requests/<int:pk>/respond/", contact_request_respond, name="contact_request_respond"),
    path("open-players/", open_players, name="open_players"),
    path("protected/", views.protected, name="protected"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include(router.urls)),
]
