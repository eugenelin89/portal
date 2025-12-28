from django.contrib import admin

from tryouts.models import TryoutEvent


@admin.register(TryoutEvent)
class TryoutEventAdmin(admin.ModelAdmin):
    list_display = ("name", "region", "association", "team", "start_date", "is_active")
    list_filter = ("region", "association", "is_active")
    search_fields = ("name", "location")
