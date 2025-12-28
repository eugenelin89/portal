from rest_framework.permissions import BasePermission, SAFE_METHODS

from accounts.permissions import IsAdminRole


class TryoutReadOnlyOrAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return IsAdminRole().has_permission(request, view)
