from django.http import Http404
from django.shortcuts import get_object_or_404, render

from tryouts.models import TryoutEvent


def _get_region(request):
    if getattr(request, "region", None):
        return request.region
    return None


def tryout_list(request):
    region = _get_region(request)
    if region is None:
        queryset = TryoutEvent.objects.none()
        base_queryset = queryset
    else:
        queryset = TryoutEvent.objects.filter(region=region, is_active=True).order_by(
            "start_date",
            "name",
        )
        base_queryset = TryoutEvent.objects.filter(region=region, is_active=True)

    age_group = request.GET.get("age_group") or ""
    level = request.GET.get("level") or ""
    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""

    if age_group:
        queryset = queryset.filter(team__age_group=age_group)
    if level:
        queryset = queryset.filter(team__level=level)
    if date_from:
        queryset = queryset.filter(start_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(start_date__lte=date_to)

    age_groups = (
        base_queryset.filter(team__isnull=False)
        .values_list("team__age_group", flat=True)
        .distinct()
    )
    levels = (
        base_queryset.filter(team__isnull=False)
        .exclude(team__level="")
        .values_list("team__level", flat=True)
        .distinct()
    )

    context = {
        "tryouts": queryset,
        "age_groups": sorted(age_groups),
        "levels": sorted(levels),
        "filters": {
            "age_group": age_group,
            "level": level,
            "date_from": date_from,
            "date_to": date_to,
        },
        "page_title": "Tryouts",
        "page_subtitle": "Browse upcoming tryouts and registration links.",
    }
    return render(request, "tryouts/list.html", context)


def tryout_detail(request, tryout_id: int):
    region = _get_region(request)
    if region is None:
        raise Http404

    tryout = get_object_or_404(
        TryoutEvent.objects.filter(region=region, is_active=True),
        pk=tryout_id,
    )
    context = {
        "tryout": tryout,
        "page_title": tryout.name,
        "page_subtitle": "Tryout details and registration.",
    }
    return render(request, "tryouts/detail.html", context)
