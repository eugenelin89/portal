from django.http import Http404
from django.shortcuts import get_object_or_404, render

from accounts.web_helpers import get_region_or_404
from organizations.models import Association
from tryouts.models import TryoutEvent


def association_detail(request, association_id: int):
    region = get_region_or_404(request)
    association = get_object_or_404(
        Association.objects.filter(region=region, is_active=True),
        pk=association_id,
    )
    tryouts = TryoutEvent.objects.filter(
        region=region,
        association=association,
        is_active=True,
    ).order_by("start_date", "name")
    context = {
        "association": association,
        "tryouts": tryouts,
        "page_title": association.name,
        "page_subtitle": "Association information and contact details.",
    }
    return render(request, "organizations/detail.html", context)


def region_home(request):
    region = get_region_or_404(request)
    associations = Association.objects.filter(region=region, is_active=True).order_by("name")
    context = {
        "associations": associations,
        "region": region,
    }
    return render(request, "home.html", context)
