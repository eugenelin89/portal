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
    current_association = models.ForeignKey(
        "organizations.Association",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_players",
    )
    display_name = models.CharField(max_length=100, blank=True)
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)
    positions = models.JSONField(null=True, blank=True)
    bats = models.CharField(max_length=1, choices=Bats.choices, blank=True)
    throws = models.CharField(max_length=1, choices=Throws.choices, blank=True)
    class Visibility(models.TextChoices):
        ALL = "all", "All associations"
        NONE = "none", "No associations"
        SPECIFIC = "specific", "Specific associations"

    profile_visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.NONE,
    )
    visible_associations = models.ManyToManyField(
        "organizations.Association",
        blank=True,
        related_name="visible_player_profiles",
    )
    pbr_url = models.URLField(blank=True)
    pg_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    instagram_handle = models.CharField(max_length=80, blank=True)
    twitter_handle = models.CharField(max_length=80, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user_id"]

    def __str__(self) -> str:
        return self.display_name or self.user.username
