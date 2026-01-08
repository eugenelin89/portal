from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.models import AccountProfile


@login_required
def dashboard_router(request):
    user = request.user
    role = getattr(user, "profile", None)
    if user.is_staff or user.is_superuser or (role and role.role == AccountProfile.Roles.ADMIN):
        return redirect("/admin/")
    if role and role.role == AccountProfile.Roles.COACH:
        return redirect("coach_dashboard")
    return redirect("player_dashboard")


@login_required
def player_dashboard(request):
    return render(request, "dashboards/player.html")


@login_required
def coach_dashboard(request):
    return render(request, "dashboards/coach.html")
