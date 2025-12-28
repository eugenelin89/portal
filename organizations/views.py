from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from organizations.models import Association, Team
from organizations.serializers import AssociationSerializer, TeamSerializer
from regions.utils import RegionScopedQuerysetMixin


class AssociationViewSet(RegionScopedQuerysetMixin, ReadOnlyModelViewSet):
    queryset = Association.objects.all()
    serializer_class = AssociationSerializer
    permission_classes = [IsAuthenticated]


class TeamViewSet(RegionScopedQuerysetMixin, ReadOnlyModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
