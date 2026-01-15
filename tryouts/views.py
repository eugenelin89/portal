from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from contacts.models import AuditLog
from regions.utils import RegionScopedQuerysetMixin
from tryouts.models import TryoutEvent
from tryouts.permissions import TryoutWritePermission
from tryouts.serializers import TryoutEventSerializer


class TryoutEventViewSet(RegionScopedQuerysetMixin, ModelViewSet):
    queryset = TryoutEvent.objects.filter(is_active=True).order_by("start_date")
    serializer_class = TryoutEventSerializer
    permission_classes = [TryoutWritePermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        age_group = params.get("age_group")
        level = params.get("level")
        date_from = params.get("date_from")
        date_to = params.get("date_to")

        if age_group:
            queryset = queryset.filter(team__age_group=age_group)
        if level:
            queryset = queryset.filter(team__level=level)
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(start_date__lte=date_to)

        return queryset

    def perform_create(self, serializer):
        region = getattr(self.request, "region", None)
        if region is None:
            raise serializers.ValidationError("Region is required.")

        team = serializer.validated_data.get("team")
        association = serializer.validated_data.get("association")
        if team is None:
            if not (self.request.user.is_staff or self.request.user.is_superuser):
                raise serializers.ValidationError({"team": "Team is required."})
            if association is None:
                raise serializers.ValidationError({"association": "Association is required."})
            if association.region_id != region.id:
                raise serializers.ValidationError(
                    {"association": "Association must belong to the current region."}
                )
            tryout = serializer.save(region=region)
        else:
            if team.region_id != region.id:
                raise serializers.ValidationError({"team": "Team must belong to the current region."})
            tryout = serializer.save(region=region, association=team.association)

        AuditLog.objects.create(
            actor=self.request.user,
            action="TRYOUT_CREATED",
            target_type=tryout.__class__.__name__,
            target_id=tryout.id,
            region=region,
        )

    def perform_update(self, serializer):
        region = getattr(self.request, "region", None)
        if region is None:
            raise serializers.ValidationError("Region is required.")

        team = serializer.validated_data.get("team")
        if team is not None:
            if team.region_id != region.id:
                raise serializers.ValidationError({"team": "Team must belong to the current region."})
            tryout = serializer.save(region=region, association=team.association)
        else:
            tryout = serializer.save(region=region)

        action = "TRYOUT_UPDATED"
        if serializer.validated_data.get("is_active") is False:
            action = "TRYOUT_CANCELED"
        AuditLog.objects.create(
            actor=self.request.user,
            action=action,
            target_type=tryout.__class__.__name__,
            target_id=tryout.id,
            region=region,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        AuditLog.objects.create(
            actor=request.user,
            action="TRYOUT_CANCELED",
            target_type=instance.__class__.__name__,
            target_id=instance.id,
            region=instance.region,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
