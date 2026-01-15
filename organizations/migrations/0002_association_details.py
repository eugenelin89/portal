from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="association",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="association",
            name="contact_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="association",
            name="contact_phone",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="association",
            name="address",
            field=models.TextField(blank=True),
        ),
    ]
