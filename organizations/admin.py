from django.contrib import admin

from organizations.models import Association, Team, TeamCoach


@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    list_display = ("name", "region", "official_domain", "is_active")
    list_filter = ("region", "is_active")
    search_fields = ("name", "short_name", "official_domain")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "age_group", "level", "association", "region", "is_active")
    list_filter = ("region", "association", "age_group", "level", "is_active")
    search_fields = ("name",)


@admin.register(TeamCoach)
class TeamCoachAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "is_active")
    list_filter = ("is_active",)
    search_fields = ("user__username", "team__name")
