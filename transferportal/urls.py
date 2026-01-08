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
    path("coach/", account_views.coach_dashboard, name="coach_dashboard"),
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
