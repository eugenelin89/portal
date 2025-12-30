from rest_framework import serializers

from profiles.models import PlayerProfile


class PlayerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerProfile
        fields = (
            "id",
            "display_name",
            "birth_year",
            "positions",
            "bats",
            "throws",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
