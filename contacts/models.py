from django.conf import settings
from django.db import models

from organizations.models import Team
from regions.models import Region


class ContactRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        DECLINED = "declined", "Declined"

    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contact_requests",
    )
    requesting_team = models.ForeignKey(
        Team,
        on_delete=models.PROTECT,
        related_name="contact_requests",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_contact_requests",
    )
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="contact_requests")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    message = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["player", "requesting_team"],
                condition=models.Q(status="pending"),
                name="unique_pending_request_per_player_team",
            )
        ]

    def __str__(self) -> str:
        return f"Request {self.requesting_team.name} -> {self.player.username} ({self.status})"


class AuditLog(models.Model):
    action = models.CharField(max_length=50)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    target_type = models.CharField(max_length=100)
    target_id = models.PositiveBigIntegerField()
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="audit_logs")
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.action} ({self.target_type}:{self.target_id})"
