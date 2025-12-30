from django.contrib import admin

from availability.models import PlayerAvailability


@admin.register(PlayerAvailability)
class PlayerAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("player", "region", "is_open", "is_committed", "committed_at", "expires_at", "updated_at")
    list_filter = ("region", "is_open", "is_committed")
    search_fields = ("player__username",)
    readonly_fields = (
        "player",
        "region",
        "is_open",
        "is_committed",
        "committed_at",
        "positions",
        "levels",
        "expires_at",
        "allowed_teams",
        "created_at",
        "updated_at",
    )
