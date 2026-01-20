from django.db import models
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, ListModelMixin

from accounts.models import AccountProfile
from accounts.permissions import IsAdminRole, IsApprovedCoach
from availability.models import PlayerAvailability
from availability.permissions import AvailabilitySearchPermission
from availability.serializers import PlayerAvailabilitySearchSerializer
from contacts.models import AuditLog, ContactRequest
from contacts.serializers import (
    ContactRequestCreateSerializer,
    ContactRequestRespondSerializer,
    ContactRequestSerializer,
)
from organizations.models import TeamCoach
from regions.utils import get_request_region


AUDIT_CONTACT_REQUEST_CREATED = "CONTACT_REQUEST_CREATED"
AUDIT_CONTACT_REQUEST_APPROVED = "CONTACT_REQUEST_APPROVED"
AUDIT_CONTACT_REQUEST_DECLINED = "CONTACT_REQUEST_DECLINED"


def log_audit(actor, action, target, region, metadata=None):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target.__class__.__name__,
        target_id=target.id,
        region=region,
        metadata=metadata,
    )


class ContactRequestViewSet(CreateModelMixin, ListModelMixin, GenericViewSet):
    queryset = ContactRequest.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return ContactRequestCreateSerializer
        return ContactRequestSerializer

    def get_queryset(self):
        region = get_request_region(self.request)
        if region is None:
            return ContactRequest.objects.none()

        user = self.request.user
        if user.is_staff or user.is_superuser:
            return ContactRequest.objects.filter(region=region, requested_by=user)

        profile = getattr(user, "profile", None)
        if profile and profile.role == AccountProfile.Roles.PLAYER:
            return ContactRequest.objects.filter(region=region, player=user)
        return ContactRequest.objects.filter(region=region, requested_by=user)

    def create(self, request, *args, **kwargs):
        if not (IsApprovedCoach().has_permission(request, self) or IsAdminRole().has_permission(request, self)):
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        contact_request = serializer.save()

        log_audit(
            actor=request.user,
            action=AUDIT_CONTACT_REQUEST_CREATED,
            target=contact_request,
            region=contact_request.region,
            metadata={"requesting_team_id": contact_request.requesting_team_id},
        )
        output = ContactRequestSerializer(contact_request, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def contact_request_respond(request, pk):
    region = get_request_region(request)
    contact_request = ContactRequest.objects.filter(id=pk, region=region).first()
    if contact_request is None:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ContactRequestRespondSerializer(
        data=request.data,
        context={"request": request, "contact_request": contact_request},
    )
    serializer.is_valid(raise_exception=True)
    contact_request = serializer.save()

    action = (
        AUDIT_CONTACT_REQUEST_APPROVED
        if contact_request.status == ContactRequest.Status.APPROVED
        else AUDIT_CONTACT_REQUEST_DECLINED
    )
    log_audit(actor=request.user, action=action, target=contact_request, region=contact_request.region)

    output = ContactRequestSerializer(contact_request, context={"request": request})
    return Response(output.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated, AvailabilitySearchPermission])
def open_players(request):
    region = get_request_region(request)
    if region is None:
        return Response([], status=status.HTTP_200_OK)

    now = timezone.now()
    queryset = PlayerAvailability.objects.filter(
        region=region,
        is_open=True,
        is_committed=False,
    ).filter(
        models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
    )

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
