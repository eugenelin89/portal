from rest_framework.permissions import BasePermission

from accounts.models import AccountProfile
from accounts.utils import get_effective_role


class IsAdminRole(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        return get_effective_role(request.user) == AccountProfile.Roles.ADMIN


class IsCoachRole(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if not hasattr(request.user, "profile"):
            return False
        return request.user.profile.role == AccountProfile.Roles.COACH


class IsApprovedCoach(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not IsCoachRole().has_permission(request, view):
            return False
        return request.user.profile.is_coach_approved


class IsSelf(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        return obj == request.user
