from django.db import migrations, models


def copy_allowed_associations(apps, schema_editor):
    PlayerAvailability = apps.get_model("availability", "PlayerAvailability")
    for availability in PlayerAvailability.objects.all():
        association_ids = (
            availability.allowed_teams.values_list("association_id", flat=True)
            .distinct()
        )
        if association_ids:
            availability.allowed_associations.add(*association_ids)


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("availability", "0003_is_open_default_true"),
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="playeravailability",
            name="allowed_associations",
            field=models.ManyToManyField(
                blank=True,
                related_name="allowed_availabilities",
                to="organizations.association",
            ),
        ),
        migrations.RunPython(copy_allowed_associations, noop_reverse),
        migrations.RemoveField(
            model_name="playeravailability",
            name="allowed_teams",
        ),
    ]
