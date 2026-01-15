from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0003_merge_0002_association_details_0002_association_domains"),
    ]

    operations = [
        migrations.AddField(
            model_name="association",
            name="logo",
            field=models.ImageField(blank=True, upload_to="associations/logos/"),
        ),
    ]
