from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import AccountProfile
from profiles.models import PlayerProfile
from profiles.serializers import PlayerProfileSerializer


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def profile_me(request):
    if request.user.is_staff or request.user.is_superuser:
        return Response({"detail": "Players only."}, status=403)

    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != AccountProfile.Roles.PLAYER:
        return Response({"detail": "Players only."}, status=403)

    player_profile, _ = PlayerProfile.objects.get_or_create(user=request.user)

    if request.method == "PATCH":
        serializer = PlayerProfileSerializer(
            instance=player_profile,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    serializer = PlayerProfileSerializer(player_profile)
    return Response(serializer.data)
