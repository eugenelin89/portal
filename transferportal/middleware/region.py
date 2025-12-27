from __future__ import annotations

from typing import Optional

from regions.models import Region


class RegionMiddleware:
    """Attach region context to the request based on the subdomain."""

    default_region_code = "bc"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0]
        subdomain = self._get_subdomain(host)
        region = self._get_active_region(subdomain)

        if region is None:
            region = self._get_active_region(self.default_region_code)
            request.region_code = self.default_region_code
        else:
            request.region_code = region.code

        request.region = region
        return self.get_response(request)

    @staticmethod
    def _get_subdomain(host: str) -> Optional[str]:
        parts = host.split(".")
        if len(parts) < 2:
            return None
        return parts[0].lower()

    @staticmethod
    def _get_active_region(code: Optional[str]) -> Optional[Region]:
        if not code:
            return None
        return Region.objects.filter(code=code.lower(), is_active=True).first()
