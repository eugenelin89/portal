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
            name="PlayerAvailability",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_open", models.BooleanField(default=False)),
                ("positions", models.JSONField(blank=True, null=True)),
                ("levels", models.JSONField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("player", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="availability", to=settings.AUTH_USER_MODEL)),
                ("region", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="availabilities", to="regions.region")),
            ],
            options={
                "ordering": ["-updated_at"],
            },
        ),
        migrations.AddField(
            model_name="playeravailability",
            name="allowed_teams",
            field=models.ManyToManyField(blank=True, related_name="allowed_availabilities", to="organizations.team"),
        ),
    ]
