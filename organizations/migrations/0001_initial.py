from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("regions", "0002_seed_bc_region"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Association",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("short_name", models.CharField(blank=True, max_length=50)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("region", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="associations", to="regions.region")),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Team",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("age_group", models.CharField(max_length=10)),
                ("level", models.CharField(blank=True, max_length=20)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("association", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="teams", to="organizations.association")),
                ("region", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="teams", to="regions.region")),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="TeamCoach",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("team", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="coach_memberships", to="organizations.team")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="team_memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["team", "user"],
                "unique_together": {("user", "team")},
            },
        ),
    ]
