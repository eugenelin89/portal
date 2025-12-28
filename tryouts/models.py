from django.core.exceptions import ValidationError
from django.db import models

from organizations.models import Association, Team
from regions.models import Region


class TryoutEvent(models.Model):
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="tryouts")
    association = models.ForeignKey(Association, on_delete=models.PROTECT, related_name="tryouts")
    team = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="tryouts", null=True, blank=True)
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.TextField()
    registration_url = models.URLField()
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_date", "name"]

    def clean(self):
        if self.association_id and self.region_id and self.association.region_id != self.region_id:
            raise ValidationError({"region": "Tryout region must match association region."})
        if self.team_id and self.region_id and self.team.region_id != self.region_id:
            raise ValidationError({"team": "Team region must match tryout region."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
