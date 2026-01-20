from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("availability", "0002_add_committed_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="playeravailability",
            name="is_open",
            field=models.BooleanField(default=True),
        ),
    ]
