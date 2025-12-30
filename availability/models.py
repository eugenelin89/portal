from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from accounts.models import AccountProfile
from organizations.models import Team
from regions.models import Region


class PlayerAvailability(models.Model):
    player = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="availability",
    )
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="availabilities")
    is_open = models.BooleanField(default=False)
    is_committed = models.BooleanField(default=False)
    committed_at = models.DateTimeField(null=True, blank=True)
    positions = models.JSONField(null=True, blank=True)
    levels = models.JSONField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    allowed_teams = models.ManyToManyField(Team, blank=True, related_name="allowed_availabilities")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def clean(self):
        profile = getattr(self.player, "profile", None)
        if profile and profile.role != AccountProfile.Roles.PLAYER:
            raise ValidationError({"player": "Only players can have availability records."})

    @property
    def is_open_effective(self) -> bool:
        if self.is_committed:
            return False
        if not self.is_open:
            return False
        if self.expires_at and self.expires_at <= timezone.now():
            return False
        return True

    def __str__(self) -> str:
        return f"Availability for {self.player.username}"
