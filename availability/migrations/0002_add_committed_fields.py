from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("availability", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="playeravailability",
            name="is_committed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="playeravailability",
            name="committed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
