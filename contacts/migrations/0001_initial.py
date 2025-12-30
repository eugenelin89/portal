from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("organizations", "0001_initial"),
        ("regions", "0002_seed_bc_region"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("declined", "Declined")], default="pending", max_length=20)),
                ("message", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                ("player", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="contact_requests", to=settings.AUTH_USER_MODEL)),
                ("region", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="contact_requests", to="regions.region")),
                ("requested_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sent_contact_requests", to=settings.AUTH_USER_MODEL)),
                ("requesting_team", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="contact_requests", to="organizations.team")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=50)),
                ("target_type", models.CharField(max_length=100)),
                ("target_id", models.PositiveBigIntegerField()),
                ("metadata", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_logs", to=settings.AUTH_USER_MODEL)),
                ("region", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="audit_logs", to="regions.region")),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="contactrequest",
            constraint=models.UniqueConstraint(condition=models.Q(("status", "pending")), fields=("player", "requesting_team"), name="unique_pending_request_per_player_team"),
        ),
    ]
