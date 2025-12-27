"""URL configuration for transferportal project."""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.urls")),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]
