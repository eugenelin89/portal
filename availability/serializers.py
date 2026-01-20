from rest_framework import serializers

from availability.models import PlayerAvailability
from organizations.models import Association


class PlayerAvailabilityMeSerializer(serializers.ModelSerializer):
    allowed_associations = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Association.objects.all(),
        required=False,
    )

    class Meta:
        model = PlayerAvailability
        fields = (
            "id",
            "region",
            "is_open",
            "is_committed",
            "committed_at",
            "positions",
            "levels",
            "expires_at",
            "allowed_associations",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "region", "committed_at", "created_at", "updated_at")

    def validate_allowed_associations(self, associations):
        request = self.context.get("request")
        region = getattr(request, "region", None)
        if region is None:
            return associations
        for association in associations:
            if association.region_id != region.id:
                raise serializers.ValidationError("Allowed associations must match the current region.")
        return associations


class PlayerAvailabilitySearchSerializer(serializers.ModelSerializer):
    player_id = serializers.IntegerField(source="player.id", read_only=True)
    region_code = serializers.CharField(source="region.code", read_only=True)
    age_group = serializers.SerializerMethodField()

    class Meta:
        model = PlayerAvailability
        fields = (
            "player_id",
            "positions",
            "levels",
            "age_group",
            "region_code",
        )

    def get_age_group(self, obj):
        return None
