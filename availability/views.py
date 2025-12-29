from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdminRole, IsApprovedCoach
from availability.models import PlayerAvailability
from availability.permissions import AvailabilitySearchPermission, IsPlayerRole
from availability.serializers import (
    PlayerAvailabilityMeSerializer,
    PlayerAvailabilitySearchSerializer,
)
from organizations.models import TeamCoach


def _base_open_queryset(region):
    now = timezone.now()
    return PlayerAvailability.objects.filter(
        region=region,
        is_open=True,
    ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated, IsPlayerRole])
def availability_me(request):
    region = getattr(request, "region", None)
    availability, created = PlayerAvailability.objects.get_or_create(
        player=request.user,
        defaults={"region": region},
    )
    if not created and availability.region_id != getattr(region, "id", None):
        return Response({"detail": "Availability region mismatch."}, status=400)

    if request.method == "PATCH":
        serializer = PlayerAvailabilityMeSerializer(
            instance=availability,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    serializer = PlayerAvailabilityMeSerializer(availability, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, AvailabilitySearchPermission])
def availability_search(request):
    region = getattr(request, "region", None)
    queryset = _base_open_queryset(region)

    if IsApprovedCoach().has_permission(request, None) and not IsAdminRole().has_permission(request, None):
        team_ids = TeamCoach.objects.filter(
            user=request.user,
            is_active=True,
            team__region=region,
        ).values_list("team_id", flat=True)
        queryset = queryset.filter(allowed_teams__in=team_ids).distinct()

    serializer = PlayerAvailabilitySearchSerializer(queryset, many=True)
    return Response(serializer.data)
