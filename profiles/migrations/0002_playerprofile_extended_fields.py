from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0002_association_domains"),
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="playerprofile",
            name="current_association",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="current_players",
                to="organizations.association",
            ),
        ),
        migrations.AddField(
            model_name="playerprofile",
            name="profile_visibility",
            field=models.CharField(
                choices=[
                    ("all", "All associations"),
                    ("none", "No associations"),
                    ("specific", "Specific associations"),
                ],
                default="none",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="playerprofile",
            name="visible_associations",
            field=models.ManyToManyField(
                blank=True,
                related_name="visible_player_profiles",
                to="organizations.association",
            ),
        ),
        migrations.AddField(
            model_name="playerprofile",
            name="pbr_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="playerprofile",
            name="pg_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="playerprofile",
            name="youtube_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="playerprofile",
            name="instagram_handle",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="playerprofile",
            name="twitter_handle",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="playerprofile",
            name="bio",
            field=models.TextField(blank=True),
        ),
    ]
