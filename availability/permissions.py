from rest_framework.permissions import BasePermission

from accounts.models import AccountProfile
from accounts.permissions import IsAdminRole, IsApprovedCoach


class IsPlayerRole(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        profile = getattr(request.user, "profile", None)
        return bool(profile and profile.role == AccountProfile.Roles.PLAYER)


class AvailabilitySearchPermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        if IsAdminRole().has_permission(request, view):
            return True
        return IsApprovedCoach().has_permission(request, view)
