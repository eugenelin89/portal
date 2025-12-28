from rest_framework.viewsets import ModelViewSet

from regions.utils import RegionScopedQuerysetMixin
from tryouts.models import TryoutEvent
from tryouts.permissions import TryoutReadOnlyOrAdmin
from tryouts.serializers import TryoutEventSerializer


class TryoutEventViewSet(RegionScopedQuerysetMixin, ModelViewSet):
    queryset = TryoutEvent.objects.filter(is_active=True).order_by("start_date")
    serializer_class = TryoutEventSerializer
    permission_classes = [TryoutReadOnlyOrAdmin]
