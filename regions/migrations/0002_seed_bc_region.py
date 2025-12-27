from django.db import migrations


def create_bc_region(apps, schema_editor):
    Region = apps.get_model("regions", "Region")
    Region.objects.update_or_create(
        code="bc",
        defaults={"name": "British Columbia", "is_active": True},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("regions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_bc_region, migrations.RunPython.noop),
    ]
