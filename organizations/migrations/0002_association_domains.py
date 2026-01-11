from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="association",
            name="official_domain",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="association",
            name="website_url",
            field=models.URLField(blank=True),
        ),
    ]
