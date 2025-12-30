from django.conf import settings
from django.db import models


class PlayerProfile(models.Model):
    class Bats(models.TextChoices):
        RIGHT = "R", "Right"
        LEFT = "L", "Left"
        SWITCH = "S", "Switch"

    class Throws(models.TextChoices):
        RIGHT = "R", "Right"
        LEFT = "L", "Left"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="player_profile",
    )
    display_name = models.CharField(max_length=100, blank=True)
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)
    positions = models.JSONField(null=True, blank=True)
    bats = models.CharField(max_length=1, choices=Bats.choices, blank=True)
    throws = models.CharField(max_length=1, choices=Throws.choices, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user_id"]

    def __str__(self) -> str:
        return self.display_name or self.user.username
