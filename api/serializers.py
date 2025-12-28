from rest_framework import serializers

from accounts.utils import get_effective_role


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    role = serializers.CharField(read_only=True)
    is_coach_approved = serializers.BooleanField(read_only=True)
    region_code = serializers.CharField(read_only=True)

    def update(self, instance, validated_data):
        email = validated_data.get("email")
        if email is not None:
            instance.email = email
            instance.save(update_fields=["email"])
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["role"] = get_effective_role(instance)
        profile = getattr(instance, "profile", None)
        data["is_coach_approved"] = bool(profile and profile.is_coach_approved)
        request = self.context.get("request")
        data["region_code"] = getattr(request, "region_code", None)
        return data
