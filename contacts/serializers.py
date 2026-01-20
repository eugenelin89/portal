from django.db import IntegrityError
from django.utils import timezone
from rest_framework import serializers

from availability.models import PlayerAvailability
from contacts.models import ContactRequest
from contacts.utils import send_contact_request_email
from organizations.models import Team, TeamCoach
from regions.utils import get_request_region


class ContactRequestSerializer(serializers.ModelSerializer):
    player_id = serializers.IntegerField(source="player.id", read_only=True)
    requesting_team_id = serializers.IntegerField(source="requesting_team.id", read_only=True)
    requested_by_id = serializers.IntegerField(source="requested_by.id", read_only=True)
    player_email = serializers.SerializerMethodField()
    player_phone = serializers.SerializerMethodField()

    class Meta:
        model = ContactRequest
        fields = (
            "id",
            "player_id",
            "requesting_team_id",
            "requested_by_id",
            "status",
            "message",
            "created_at",
            "responded_at",
            "player_email",
            "player_phone",
        )

    def get_player_email(self, obj):
        request = self.context.get("request")
        if obj.status != ContactRequest.Status.APPROVED:
            return None
        if request and request.user and request.user.is_authenticated:
            if request.user == obj.requested_by or request.user.is_staff or request.user.is_superuser:
                return obj.player.email
        return None

    def get_player_phone(self, obj):
        request = self.context.get("request")
        if obj.status != ContactRequest.Status.APPROVED:
            return None
        if request and request.user and request.user.is_authenticated:
            if request.user == obj.requested_by or request.user.is_staff or request.user.is_superuser:
                profile = getattr(obj.player, "profile", None)
                return profile.phone_number if profile and profile.phone_number else None
        return None


class ContactRequestCreateSerializer(serializers.ModelSerializer):
    player_id = serializers.IntegerField(write_only=True)
    requesting_team_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ContactRequest
        fields = ("player_id", "requesting_team_id", "message")

    def validate(self, attrs):
        request = self.context.get("request")
        region = get_request_region(request)
        if region is None:
            raise serializers.ValidationError("Region is required.")

        try:
            team = Team.objects.get(id=attrs["requesting_team_id"], region=region)
        except Team.DoesNotExist:
            raise serializers.ValidationError("Requesting team not found in region.")

        player_availability = PlayerAvailability.objects.filter(
            player_id=attrs["player_id"],
            region=region,
        ).first()
        if not player_availability:
            raise serializers.ValidationError("Player is not currently open.")
        if player_availability.is_committed:
            raise serializers.ValidationError("Player is committed and unavailable.")
        if not player_availability.is_open_effective:
            raise serializers.ValidationError("Player is not currently open.")

        if not player_availability.allowed_associations.filter(id=team.association_id).exists():
            raise serializers.ValidationError("Player has not allowed this association to view availability.")

        if not TeamCoach.objects.filter(
            user=request.user,
            team=team,
            is_active=True,
        ).exists() and not (request.user.is_staff or request.user.is_superuser):
            raise serializers.ValidationError("Coach is not associated with the requesting team.")

        attrs["_team"] = team
        attrs["_player"] = player_availability.player
        attrs["_region"] = region
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        team = validated_data.pop("_team")
        player = validated_data.pop("_player")
        region = validated_data.pop("_region")
        try:
            contact_request = ContactRequest.objects.create(
                player=player,
                requesting_team=team,
                requested_by=request.user,
                region=region,
                status=ContactRequest.Status.PENDING,
                message=validated_data.get("message", ""),
            )
            send_contact_request_email(request, contact_request)
            return contact_request
        except IntegrityError:
            raise serializers.ValidationError("A pending request already exists for this player and team.")


class ContactRequestRespondSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[ContactRequest.Status.APPROVED, ContactRequest.Status.DECLINED])

    def validate(self, attrs):
        request = self.context.get("request")
        contact_request = self.context.get("contact_request")
        if contact_request.status != ContactRequest.Status.PENDING:
            raise serializers.ValidationError("Only pending requests can be responded to.")
        if contact_request.player != request.user:
            raise serializers.ValidationError("You can only respond to your own requests.")
        return attrs

    def save(self, **kwargs):
        contact_request = self.context.get("contact_request")
        contact_request.status = self.validated_data["status"]
        contact_request.responded_at = timezone.now()
        contact_request.save(update_fields=["status", "responded_at"])
        return contact_request
