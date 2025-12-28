from accounts.models import AccountProfile


def get_effective_role(user) -> str:
    if user.is_staff or user.is_superuser:
        return AccountProfile.Roles.ADMIN
    if hasattr(user, "profile"):
        return user.profile.role
    return AccountProfile.Roles.PLAYER
