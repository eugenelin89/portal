from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from PIL import Image

from regions.models import Region


class Association(models.Model):
    LOGO_MIN_SIZE = 200
    LOGO_MAX_SIZE = 800

    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="associations")
    name = models.CharField(max_length=150)
    short_name = models.CharField(max_length=50, blank=True)
    official_domain = models.CharField(max_length=150, blank=True)
    website_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    logo = models.ImageField(
        upload_to="associations/logos/",
        blank=True,
        help_text="Square image, 200–800px.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def clean(self):
        if self.logo and hasattr(self.logo, "file"):
            image = Image.open(self.logo)
            width, height = image.size
            if width != height:
                raise ValidationError({"logo": "Logo must be square (equal width and height)."})
            if width < self.LOGO_MIN_SIZE or width > self.LOGO_MAX_SIZE:
                raise ValidationError(
                    {"logo": f"Logo must be between {self.LOGO_MIN_SIZE}px and {self.LOGO_MAX_SIZE}px."}
                )


class Team(models.Model):
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="teams")
    association = models.ForeignKey(Association, on_delete=models.PROTECT, related_name="teams")
    name = models.CharField(max_length=150)
    age_group = models.CharField(max_length=10)
    level = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def clean(self):
        if self.association_id and self.region_id and self.association.region_id != self.region_id:
            raise ValidationError({"region": "Team region must match association region."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.age_group})"


class TeamCoach(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_memberships",
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="coach_memberships")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "team")
        ordering = ["team", "user"]

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.team.name}"
