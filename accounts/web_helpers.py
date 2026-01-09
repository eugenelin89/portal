from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden

from accounts.models import AccountProfile
from regions.utils import get_request_region


def get_region_or_404(request):
    region = get_request_region(request)
    if region is None:
        raise Http404
    return region


def require_player(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        if not profile or profile.role != AccountProfile.Roles.PLAYER:
            return HttpResponseForbidden("Players only.")
        return view_func(request, *args, **kwargs)

    return _wrapped


def require_approved_coach(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        if (
            not profile
            or profile.role != AccountProfile.Roles.COACH
            or not profile.is_coach_approved
        ):
            return HttpResponseForbidden("Approved coaches only.")
        return view_func(request, *args, **kwargs)

    return _wrapped


def require_region_object(request, obj):
    region = get_region_or_404(request)
    if getattr(obj, "region_id", None) != region.id:
        raise Http404
    return region
