"""URL configuration for transferportal project."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import TemplateView

from accounts import views as account_views
from tryouts import web_views as tryout_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.urls")),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("tryouts/", tryout_views.tryout_list, name="tryout_list"),
    path("tryouts/<int:tryout_id>/", tryout_views.tryout_detail, name="tryout_detail"),
    path("dashboard/", account_views.dashboard_router, name="dashboard"),
    path("player/", account_views.player_dashboard, name="player_dashboard"),
    path("player/profile/", account_views.player_profile, name="player_profile"),
    path("player/availability/", account_views.player_availability, name="player_availability"),
    path(
        "player/availability/commit/",
        account_views.player_availability_commit,
        name="player_availability_commit",
    ),
    path("player/requests/", account_views.player_requests, name="player_requests"),
    path(
        "player/requests/<int:request_id>/respond/",
        account_views.player_request_respond,
        name="player_request_respond",
    ),
    path("coach/", account_views.coach_dashboard, name="coach_dashboard"),
    path("coach/teams/", account_views.coach_teams, name="coach_teams"),
    path("coach/open-players/", account_views.coach_open_players, name="coach_open_players"),
    path(
        "coach/open-players/<int:player_id>/",
        account_views.coach_open_player_detail,
        name="coach_open_player_detail",
    ),
    path("coach/requests/", account_views.coach_requests, name="coach_requests"),
    path("coach/requests/new/", account_views.coach_request_new, name="coach_request_new"),
    path("coach/tryouts/", tryout_views.coach_tryout_list, name="coach_tryout_list"),
    path("coach/tryouts/new/", tryout_views.coach_tryout_create, name="coach_tryout_create"),
    path(
        "coach/tryouts/<int:tryout_id>/edit/",
        tryout_views.coach_tryout_edit,
        name="coach_tryout_edit",
    ),
    path(
        "coach/tryouts/<int:tryout_id>/cancel/",
        tryout_views.coach_tryout_cancel,
        name="coach_tryout_cancel",
    ),
    path("signup/coach/", account_views.coach_signup, name="coach_signup"),
    path("signup/coach/verify/<str:token>/", account_views.coach_verify, name="coach_verify"),
    path("signup/player/", account_views.player_signup, name="player_signup"),
    path("signup/player/verify/<str:token>/", account_views.player_verify, name="player_verify"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(next_page="home"),
        name="logout",
    ),
]
