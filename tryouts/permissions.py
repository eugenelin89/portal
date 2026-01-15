from rest_framework.permissions import BasePermission, SAFE_METHODS

from accounts.permissions import IsAdminRole, IsApprovedCoach
from organizations.models import TeamCoach
from regions.utils import get_request_region


class TryoutWritePermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        if IsAdminRole().has_permission(request, view):
            return True
        if not IsApprovedCoach().has_permission(request, view):
            return False

        if request.method == "POST":
            team_id = request.data.get("team")
            if not team_id:
                return False
            region = get_request_region(request)
            if region is None:
                return False
            return TeamCoach.objects.filter(
                user=request.user,
                team_id=team_id,
                team__region=region,
                is_active=True,
            ).exists()
        return True

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        if IsAdminRole().has_permission(request, view):
            return True
        if not IsApprovedCoach().has_permission(request, view):
            return False
        if not obj.team_id:
            return False
        return TeamCoach.objects.filter(
            user=request.user,
            team_id=obj.team_id,
            is_active=True,
        ).exists()
