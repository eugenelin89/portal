from typing import Optional

from regions.models import Region


def get_request_region(request) -> Optional[Region]:
    """Return the Region for the request if available."""
    if hasattr(request, "region"):
        return request.region
    region_code = getattr(request, "region_code", None)
    if region_code:
        return Region.objects.filter(code=region_code, is_active=True).first()
    return None


class RegionScopedQuerysetMixin:
    """Filter querysets by request.region when the model has a region field."""

    region_field = "region"

    def get_queryset(self):
        queryset = super().get_queryset()
        region = get_request_region(self.request)
        if region is None:
            return queryset
        try:
            queryset.model._meta.get_field(self.region_field)
        except Exception:
            return queryset
        return queryset.filter(**{self.region_field: region})
