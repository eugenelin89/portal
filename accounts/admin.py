from django.contrib import admin

from accounts.models import AccountProfile


@admin.register(AccountProfile)
class AccountProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone_number", "is_coach_approved", "created_at")
    list_filter = ("role", "is_coach_approved")
    search_fields = ("user__username", "user__email")
