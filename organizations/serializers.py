from rest_framework import serializers

from organizations.models import Association, Team


class AssociationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Association
        fields = (
            "id",
            "region",
            "name",
            "short_name",
            "is_active",
            "official_domain",
            "website_url",
            "description",
            "contact_email",
            "contact_phone",
            "address",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = (
            "id",
            "region",
            "association",
            "name",
            "age_group",
            "level",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
