from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.web_helpers import get_region_or_404, require_approved_coach
from contacts.models import AuditLog
from organizations.models import Team
from tryouts.forms import TryoutEventForm
from tryouts.models import TryoutEvent


def _get_region(request):
    if getattr(request, "region", None):
        return request.region
    return None


def tryout_list(request):
    region = _get_region(request)
    if region is None:
        queryset = TryoutEvent.objects.none()
        base_queryset = queryset
    else:
        queryset = TryoutEvent.objects.filter(region=region, is_active=True).order_by(
            "start_date",
            "name",
        )
        base_queryset = TryoutEvent.objects.filter(region=region, is_active=True)

    age_group = request.GET.get("age_group") or ""
    level = request.GET.get("level") or ""
    date_from = request.GET.get("date_from") or ""
    date_to = request.GET.get("date_to") or ""

    if age_group:
        queryset = queryset.filter(team__age_group=age_group)
    if level:
        queryset = queryset.filter(team__level=level)
    if date_from:
        queryset = queryset.filter(start_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(start_date__lte=date_to)

    age_groups = (
        base_queryset.filter(team__isnull=False)
        .values_list("team__age_group", flat=True)
        .distinct()
    )
    levels = (
        base_queryset.filter(team__isnull=False)
        .exclude(team__level="")
        .values_list("team__level", flat=True)
        .distinct()
    )

    context = {
        "tryouts": queryset,
        "age_groups": sorted(age_groups),
        "levels": sorted(levels),
        "filters": {
            "age_group": age_group,
            "level": level,
            "date_from": date_from,
            "date_to": date_to,
        },
        "page_title": "Tryouts",
        "page_subtitle": "Browse upcoming tryouts and registration links.",
    }
    return render(request, "tryouts/list.html", context)


def tryout_detail(request, tryout_id: int):
    region = _get_region(request)
    if region is None:
        raise Http404

    tryout = get_object_or_404(
        TryoutEvent.objects.filter(region=region, is_active=True),
        pk=tryout_id,
    )
    context = {
        "tryout": tryout,
        "page_title": tryout.name,
        "page_subtitle": "Tryout details and registration.",
    }
    return render(request, "tryouts/detail.html", context)


def _coach_teams_queryset(user, region):
    return Team.objects.filter(
        coach_memberships__user=user,
        coach_memberships__is_active=True,
        region=region,
    ).distinct()


def _log_tryout_audit(actor, action, tryout, region):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=tryout.__class__.__name__,
        target_id=tryout.id,
        region=region,
    )


@require_approved_coach
def coach_tryout_list(request):
    region = get_region_or_404(request)
    teams = _coach_teams_queryset(request.user, region)
    tryouts = TryoutEvent.objects.filter(
        region=region,
        team__in=teams,
        is_active=True,
    ).order_by("start_date", "name")
    context = {
        "tryouts": tryouts,
        "page_title": "My Tryouts",
        "page_subtitle": "Manage tryouts for your teams.",
    }
    return render(request, "coaches/tryouts.html", context)


@require_approved_coach
def coach_tryout_create(request):
    region = get_region_or_404(request)
    teams = _coach_teams_queryset(request.user, region)
    if not teams.exists():
        raise Http404

    if request.method == "POST":
        form = TryoutEventForm(request.POST, team_queryset=teams)
        if form.is_valid():
            tryout = form.save(commit=False)
            tryout.region = region
            tryout.association = tryout.team.association
            tryout.is_active = True
            tryout.save()
            _log_tryout_audit(request.user, "TRYOUT_CREATED", tryout, region)
            messages.success(request, "Tryout created.")
            return redirect("coach_tryout_list")
    else:
        form = TryoutEventForm(team_queryset=teams)

    context = {
        "form": form,
        "page_title": "New Tryout",
        "page_subtitle": "Create a tryout for one of your teams.",
    }
    return render(request, "coaches/tryout_form.html", context)


@require_approved_coach
def coach_tryout_edit(request, tryout_id: int):
    region = get_region_or_404(request)
    teams = _coach_teams_queryset(request.user, region)
    tryout = get_object_or_404(
        TryoutEvent.objects.filter(region=region, team__in=teams, is_active=True),
        pk=tryout_id,
    )

    if request.method == "POST":
        form = TryoutEventForm(request.POST, instance=tryout, team_queryset=teams)
        if form.is_valid():
            tryout = form.save(commit=False)
            tryout.region = region
            tryout.association = tryout.team.association
            tryout.save()
            _log_tryout_audit(request.user, "TRYOUT_UPDATED", tryout, region)
            messages.success(request, "Tryout updated.")
            return redirect("coach_tryout_list")
    else:
        form = TryoutEventForm(instance=tryout, team_queryset=teams)

    context = {
        "form": form,
        "tryout": tryout,
        "page_title": "Edit Tryout",
        "page_subtitle": "Update your tryout details.",
    }
    return render(request, "coaches/tryout_form.html", context)


@require_approved_coach
def coach_tryout_cancel(request, tryout_id: int):
    if request.method != "POST":
        raise Http404
    region = get_region_or_404(request)
    teams = _coach_teams_queryset(request.user, region)
    tryout = get_object_or_404(
        TryoutEvent.objects.filter(region=region, team__in=teams, is_active=True),
        pk=tryout_id,
    )
    tryout.is_active = False
    tryout.save(update_fields=["is_active"])
    _log_tryout_audit(request.user, "TRYOUT_CANCELED", tryout, region)
    messages.success(request, "Tryout canceled.")
    return redirect(reverse("coach_tryout_list"))
