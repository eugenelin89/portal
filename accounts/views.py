from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q

from accounts.models import AccountProfile
from accounts.web_helpers import get_region_or_404, require_approved_coach, require_player
from availability.forms import PlayerAvailabilityForm
from availability.models import PlayerAvailability
from availability.views import AUDIT_COMMITTED_CLEARED, AUDIT_COMMITTED_SET
from contacts.forms import ContactRequestForm, ContactRequestRespondForm
from contacts.models import AuditLog, ContactRequest
from contacts.views import AUDIT_CONTACT_REQUEST_APPROVED, AUDIT_CONTACT_REQUEST_DECLINED
from organizations.models import Team, TeamCoach
from profiles.forms import PlayerProfileForm
from profiles.models import PlayerProfile


@login_required
def dashboard_router(request):
    user = request.user
    role = getattr(user, "profile", None)
    if user.is_staff or user.is_superuser or (role and role.role == AccountProfile.Roles.ADMIN):
        return redirect("/admin/")
    if role and role.role == AccountProfile.Roles.COACH:
        return redirect("coach_dashboard")
    return redirect("player_dashboard")


@require_player
def player_dashboard(request):
    return render(request, "dashboards/player.html")


@require_approved_coach
def coach_dashboard(request):
    return render(request, "dashboards/coach.html")


@require_player
def player_profile(request):
    profile, _ = PlayerProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = PlayerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("player_profile")
    else:
        form = PlayerProfileForm(instance=profile)

    context = {
        "form": form,
        "page_title": "Player Profile",
        "page_subtitle": "Keep your player details up to date.",
    }
    return render(request, "players/profile.html", context)


@require_player
def player_availability(request):
    region = get_region_or_404(request)
    availability, created = PlayerAvailability.objects.get_or_create(
        player=request.user,
        defaults={"region": region},
    )
    if not created and availability.region_id != region.id:
        raise Http404
    if availability.is_committed and availability.is_open:
        availability.is_open = False
        availability.save(update_fields=["is_open"])

    if request.method == "POST":
        form = PlayerAvailabilityForm(request.POST, instance=availability, region=region)
        if availability.is_committed:
            form.fields["is_open"].disabled = True
        if form.is_valid():
            availability = form.save(commit=False)
            if availability.is_committed and availability.is_open:
                availability.is_open = False
            availability.region = region
            availability.save()
            form.save_m2m()
            messages.success(request, "Availability updated.")
            return redirect("player_availability")
    else:
        form = PlayerAvailabilityForm(instance=availability, region=region)
        if availability.is_committed:
            form.fields["is_open"].disabled = True

    context = {
        "availability": availability,
        "form": form,
        "page_title": "Availability",
        "page_subtitle": "Control who can see your open status.",
    }
    return render(request, "players/availability.html", context)


@require_player
def player_availability_commit(request):
    if request.method != "POST":
        raise Http404

    region = get_region_or_404(request)
    availability, _ = PlayerAvailability.objects.get_or_create(
        player=request.user,
        defaults={"region": region},
    )
    action = request.POST.get("action")
    if action == "commit":
        availability.is_committed = True
        availability.is_open = False
        availability.committed_at = timezone.now()
        availability.save(update_fields=["is_committed", "is_open", "committed_at"])
        AuditLog.objects.create(
            actor=request.user,
            action=AUDIT_COMMITTED_SET,
            target_type=availability.__class__.__name__,
            target_id=availability.id,
            region=availability.region,
        )
        messages.success(request, "Marked as committed. You are no longer searchable.")
    elif action == "uncommit":
        availability.is_committed = False
        availability.committed_at = None
        availability.save(update_fields=["is_committed", "committed_at"])
        AuditLog.objects.create(
            actor=request.user,
            action=AUDIT_COMMITTED_CLEARED,
            target_type=availability.__class__.__name__,
            target_id=availability.id,
            region=availability.region,
        )
        messages.success(request, "Committed status cleared.")
    else:
        return HttpResponseForbidden("Invalid action.")

    return redirect("player_availability")


@require_player
def player_requests(request):
    region = get_region_or_404(request)
    requests_qs = ContactRequest.objects.filter(player=request.user, region=region).select_related(
        "requesting_team",
        "requested_by",
    )
    context = {
        "requests": requests_qs,
        "page_title": "Contact Requests",
        "page_subtitle": "Respond to incoming coach requests.",
    }
    return render(request, "players/requests.html", context)


@require_player
def player_request_respond(request, request_id):
    if request.method != "POST":
        raise Http404

    region = get_region_or_404(request)
    contact_request = get_object_or_404(ContactRequest, id=request_id, region=region)
    if contact_request.player != request.user:
        return HttpResponseForbidden("You can only respond to your own requests.")
    if contact_request.status != ContactRequest.Status.PENDING:
        messages.warning(request, "That request has already been processed.")
        return redirect("player_requests")

    form = ContactRequestRespondForm(request.POST)
    if form.is_valid():
        contact_request.status = form.cleaned_data["status"]
        contact_request.responded_at = timezone.now()
        contact_request.save(update_fields=["status", "responded_at"])
        action = (
            AUDIT_CONTACT_REQUEST_APPROVED
            if contact_request.status == ContactRequest.Status.APPROVED
            else AUDIT_CONTACT_REQUEST_DECLINED
        )
        AuditLog.objects.create(
            actor=request.user,
            action=action,
            target_type=contact_request.__class__.__name__,
            target_id=contact_request.id,
            region=contact_request.region,
        )
        messages.success(request, "Response saved.")
    return redirect("player_requests")


@require_approved_coach
def coach_teams(request):
    region = get_region_or_404(request)
    memberships = (
        TeamCoach.objects.filter(user=request.user, is_active=True, team__region=region)
        .select_related("team", "team__association")
        .order_by("team__name")
    )
    context = {
        "memberships": memberships,
        "page_title": "My Teams",
        "page_subtitle": "Teams you are approved to represent.",
    }
    return render(request, "coaches/teams.html", context)


def _open_players_queryset(region):
    now = timezone.now()
    return PlayerAvailability.objects.filter(
        region=region,
        is_open=True,
        is_committed=False,
    ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))


@require_approved_coach
def coach_open_players(request):
    region = get_region_or_404(request)
    team_ids = list(TeamCoach.objects.filter(
        user=request.user,
        is_active=True,
        team__region=region,
    ).values_list("team_id", flat=True))
    if not team_ids:
        players = []
    else:
        queryset = (
            _open_players_queryset(region)
            .filter(allowed_teams__in=team_ids)
            .distinct()
            .select_related("player")
            .order_by("-updated_at")
        )
        profiles = {
            profile.user_id: profile
            for profile in PlayerProfile.objects.filter(user__in=queryset.values("player_id"))
        }
        players = [
            {"availability": availability, "profile": profiles.get(availability.player_id)}
            for availability in queryset
        ]

    context = {
        "players": players,
        "page_title": "Open Players",
        "page_subtitle": "Players who have allowed your teams to view availability.",
    }
    return render(request, "coaches/open_players.html", context)


@require_approved_coach
def coach_open_player_detail(request, player_id):
    region = get_region_or_404(request)
    team_ids = list(TeamCoach.objects.filter(
        user=request.user,
        is_active=True,
        team__region=region,
    ).values_list("team_id", flat=True))
    if not team_ids:
        raise Http404

    availability = get_object_or_404(
        PlayerAvailability.objects.select_related("player").filter(
            region=region,
            player_id=player_id,
            is_open=True,
            is_committed=False,
        ),
    )
    if availability.expires_at and availability.expires_at <= timezone.now():
        raise Http404
    if not availability.allowed_teams.filter(id__in=team_ids).exists():
        raise Http404

    profile = PlayerProfile.objects.filter(user=availability.player).first()
    context = {
        "availability": availability,
        "profile": profile,
        "page_title": "Player Availability",
        "page_subtitle": "Review details and send a request.",
    }
    return render(request, "coaches/open_player_detail.html", context)


@require_approved_coach
def coach_requests(request):
    region = get_region_or_404(request)
    requests_qs = ContactRequest.objects.filter(
        requested_by=request.user,
        region=region,
    ).select_related("player", "requesting_team")

    context = {
        "requests": requests_qs,
        "page_title": "Sent Requests",
        "page_subtitle": "Track the status of your outreach.",
    }
    return render(request, "coaches/requests.html", context)


def _available_players_for_coach(region, request):
    team_ids = list(TeamCoach.objects.filter(
        user=request.user,
        is_active=True,
        team__region=region,
    ).values_list("team_id", flat=True))
    if not team_ids:
        return {}, Team.objects.none()

    queryset = _open_players_queryset(region).filter(allowed_teams__in=team_ids).distinct()
    queryset = queryset.select_related("player", "player__player_profile")

    players = {}
    for availability in queryset:
        profile = getattr(availability.player, "player_profile", None)
        name = profile.display_name if profile and profile.display_name else availability.player.username
        label = name
        if profile and profile.birth_year:
            label = f"{label} ({profile.birth_year})"
        players[str(availability.player_id)] = label

    teams = Team.objects.filter(id__in=team_ids).order_by("name")
    return players, teams


@require_approved_coach
def coach_request_new(request):
    region = get_region_or_404(request)
    available_players, coach_teams = _available_players_for_coach(region, request)

    if request.method == "POST":
        form = ContactRequestForm(
            request.POST,
            request=request,
            available_players=available_players,
            coach_teams=coach_teams,
        )
        if form.is_valid():
            try:
                form.save(requested_by=request.user)
            except forms.ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, "Contact request sent.")
                return redirect("coach_requests")
    else:
        initial = {}
        if request.GET.get("player_id"):
            initial["player"] = request.GET.get("player_id")
        form = ContactRequestForm(
            initial=initial,
            request=request,
            available_players=available_players,
            coach_teams=coach_teams,
        )

    context = {
        "form": form,
        "has_players": bool(available_players),
        "page_title": "New Contact Request",
        "page_subtitle": "Reach out to an open player on your allow list.",
    }
    return render(request, "coaches/request_new.html", context)
