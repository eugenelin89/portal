from rest_framework import serializers

from tryouts.models import TryoutEvent


class TryoutEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TryoutEvent
        fields = (
            "id",
            "region",
            "association",
            "team",
            "name",
            "start_date",
            "end_date",
            "location",
            "registration_url",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "region")
        extra_kwargs = {
            "association": {"required": False, "allow_null": True},
            "team": {"required": False, "allow_null": True},
        }
