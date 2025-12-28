from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("organizations", "0001_initial"),
        ("regions", "0002_seed_bc_region"),
    ]

    operations = [
        migrations.CreateModel(
            name="TryoutEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("location", models.TextField()),
                ("registration_url", models.URLField()),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("association", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="tryouts", to="organizations.association")),
                ("region", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="tryouts", to="regions.region")),
                ("team", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="tryouts", to="organizations.team")),
            ],
            options={
                "ordering": ["start_date", "name"],
            },
        ),
    ]
