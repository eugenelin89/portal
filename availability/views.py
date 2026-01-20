from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdminRole, IsApprovedCoach
from contacts.models import AuditLog
from availability.models import PlayerAvailability
from availability.permissions import AvailabilitySearchPermission, IsPlayerRole
from availability.serializers import (
    PlayerAvailabilityMeSerializer,
    PlayerAvailabilitySearchSerializer,
)
from organizations.models import Association, TeamCoach
from organizations.serializers import AssociationSerializer
from regions.utils import get_request_region


AUDIT_COMMITTED_SET = "COMMITTED_SET"
AUDIT_COMMITTED_CLEARED = "COMMITTED_CLEARED"


def _base_open_queryset(region):
    now = timezone.now()
    return PlayerAvailability.objects.filter(
        region=region,
        is_open=True,
        is_committed=False,
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
        availability = serializer.save()

        if "is_committed" in serializer.validated_data:
            if availability.is_committed:
                availability.is_open = False
                availability.committed_at = timezone.now()
                action = AUDIT_COMMITTED_SET
            else:
                availability.committed_at = None
                action = AUDIT_COMMITTED_CLEARED
            availability.save(update_fields=["is_open", "is_committed", "committed_at"])
            AuditLog.objects.create(
                actor=request.user,
                action=action,
                target_type=availability.__class__.__name__,
                target_id=availability.id,
                region=availability.region,
            )
        elif availability.is_committed and availability.is_open:
            availability.is_open = False
            availability.save(update_fields=["is_open"])
        return Response(serializer.data)

    serializer = PlayerAvailabilityMeSerializer(availability, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, AvailabilitySearchPermission])
def availability_search(request):
    region = getattr(request, "region", None)
    queryset = _base_open_queryset(region)

    if IsApprovedCoach().has_permission(request, None) and not IsAdminRole().has_permission(request, None):
        association_ids = set(TeamCoach.objects.filter(
            user=request.user,
            is_active=True,
            team__region=region,
        ).values_list("team__association_id", flat=True))
        profile_association = getattr(getattr(request.user, "profile", None), "association", None)
        if profile_association and profile_association.region_id == region.id:
            association_ids.add(profile_association.id)
        queryset = queryset.filter(allowed_associations__in=association_ids).distinct()

    serializer = PlayerAvailabilitySearchSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsPlayerRole])
def availability_allowed_associations(request):
    region = get_request_region(request)
    if region is None:
        return Response({"detail": "Region is required."}, status=400)

    availability, created = PlayerAvailability.objects.get_or_create(
        player=request.user,
        defaults={"region": region},
    )
    if not created and availability.region_id != region.id:
        return Response({"detail": "Availability region mismatch."}, status=400)

    if request.method == "POST":
        association_id = request.data.get("association_id")
        if not association_id:
            return Response({"detail": "association_id is required."}, status=400)
        association = Association.objects.filter(id=association_id, region=region).first()
        if association is None:
            return Response({"detail": "Association not found in region."}, status=404)
        availability.allowed_associations.add(association)

    associations = availability.allowed_associations.filter(region=region).order_by("name")
    serializer = AssociationSerializer(associations, many=True)
    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsPlayerRole])
def availability_allowed_association_delete(request, association_id):
    region = get_request_region(request)
    if region is None:
        return Response({"detail": "Region is required."}, status=400)

    availability = PlayerAvailability.objects.filter(player=request.user, region=region).first()
    if availability is None:
        return Response({"detail": "Availability not found."}, status=404)

    association = Association.objects.filter(id=association_id, region=region).first()
    if association is None:
        return Response({"detail": "Association not found in region."}, status=404)

    availability.allowed_associations.remove(association)
    return Response(status=204)
