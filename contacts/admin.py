from django.contrib import admin

from contacts.models import AuditLog, ContactRequest


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ("player", "requesting_team", "requested_by", "status", "created_at")
    list_filter = ("status", "region")
    search_fields = ("player__username", "requesting_team__name", "requested_by__username")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "target_type", "target_id", "region", "created_at")
    list_filter = ("action", "region")
    search_fields = ("actor__username", "target_type")
    readonly_fields = (
        "action",
        "actor",
        "target_type",
        "target_id",
        "region",
        "metadata",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
