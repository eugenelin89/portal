from django.db import migrations, models


def copy_requesting_association(apps, schema_editor):
    ContactRequest = apps.get_model("contacts", "ContactRequest")
    for request in ContactRequest.objects.select_related("requesting_team"):
        if request.requesting_team_id and not request.requesting_association_id:
            request.requesting_association_id = request.requesting_team.association_id
            request.save(update_fields=["requesting_association"])


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("contacts", "0001_initial"),
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactrequest",
            name="requesting_association",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.PROTECT,
                related_name="contact_requests",
                to="organizations.association",
            ),
        ),
        migrations.AlterField(
            model_name="contactrequest",
            name="requesting_team",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.PROTECT,
                related_name="contact_requests",
                to="organizations.team",
            ),
        ),
        migrations.RunPython(copy_requesting_association, noop_reverse),
        migrations.AddConstraint(
            model_name="contactrequest",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "pending"), ("requesting_association__isnull", False)),
                fields=("player", "requesting_association"),
                name="unique_pending_request_per_player_association",
            ),
        ),
    ]
