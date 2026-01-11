from django.conf import settings
from django.db import models


class AccountProfile(models.Model):
    class Roles(models.TextChoices):
        PLAYER = "player", "Player/Parent"
        COACH = "coach", "Coach/Manager"
        ADMIN = "admin", "Admin"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.PLAYER,
    )
    phone_number = models.CharField(max_length=30, blank=True)
    is_coach_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username} ({self.role})"
