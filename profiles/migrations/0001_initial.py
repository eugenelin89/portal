from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PlayerProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(blank=True, max_length=100)),
                ("birth_year", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("positions", models.JSONField(blank=True, null=True)),
                ("bats", models.CharField(blank=True, choices=[("R", "Right"), ("L", "Left"), ("S", "Switch")], max_length=1)),
                ("throws", models.CharField(blank=True, choices=[("R", "Right"), ("L", "Left")], max_length=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="player_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["user_id"],
            },
        ),
    ]
