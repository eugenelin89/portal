from django.contrib import admin

from profiles.models import PlayerProfile


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "display_name",
        "birth_year",
        "current_association",
        "profile_visibility",
        "bats",
        "throws",
        "updated_at",
    )
    search_fields = ("user__username", "display_name")
