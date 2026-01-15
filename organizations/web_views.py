from django.http import Http404
from django.shortcuts import get_object_or_404, render

from accounts.web_helpers import get_region_or_404
from organizations.models import Association


def association_detail(request, association_id: int):
    region = get_region_or_404(request)
    association = get_object_or_404(
        Association.objects.filter(region=region, is_active=True),
        pk=association_id,
    )
    context = {
        "association": association,
        "page_title": association.name,
        "page_subtitle": "Association information and contact details.",
    }
    return render(request, "organizations/detail.html", context)
