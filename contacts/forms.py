from django import forms
from django.db import IntegrityError

from availability.models import PlayerAvailability
from contacts.models import ContactRequest
from contacts.utils import send_contact_request_email
from organizations.models import Team
from regions.utils import get_request_region


class ContactRequestForm(forms.Form):
    player = forms.ChoiceField(widget=forms.Select)
    requesting_team = forms.ModelChoiceField(queryset=Team.objects.none(), required=False)
    message = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        available_players = kwargs.pop("available_players", {})
        coach_teams = kwargs.pop("coach_teams", Team.objects.none())
        super().__init__(*args, **kwargs)
        self.request = request
        self.available_players = available_players
        self.fields["player"].choices = [
            (str(player_id), label) for player_id, label in available_players.items()
        ]
        self.fields["requesting_team"].queryset = coach_teams
        self.fields["requesting_team"].help_text = (
            "Optional. Leave blank to request on behalf of your association."
        )

        for field_name in self.fields:
            field = self.fields[field_name]
            if isinstance(field.widget, (forms.TextInput, forms.Textarea)):
                field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")

    def clean(self):
        cleaned_data = super().clean()
        request = self.request
        region = get_request_region(request)
        if region is None:
            raise forms.ValidationError("Region is required.")

        player_id = cleaned_data.get("player")
        team = cleaned_data.get("requesting_team")
        if not player_id:
            return cleaned_data

        if str(player_id) not in self.available_players:
            raise forms.ValidationError("Player is not available for contact.")

        availability = PlayerAvailability.objects.filter(
            player_id=player_id,
            region=region,
        ).first()
        if not availability or not availability.is_open_effective:
            raise forms.ValidationError("Player is not currently open.")
        if availability.is_committed:
            raise forms.ValidationError("Player is committed and unavailable.")

        association = None
        if team is not None:
            association = team.association
            if not availability.allowed_associations.filter(id=team.association_id).exists():
                raise forms.ValidationError("Player has not allowed this association to view availability.")

            if not Team.objects.filter(id=team.id, region=region).exists():
                raise forms.ValidationError("Requesting team not found in region.")

            if request and request.user:
                if not team.coach_memberships.filter(user=request.user, is_active=True).exists():
                    raise forms.ValidationError("Coach is not associated with the requesting team.")

            if ContactRequest.objects.filter(
                player_id=availability.player_id,
                requesting_team=team,
                status=ContactRequest.Status.PENDING,
            ).exists():
                raise forms.ValidationError("A pending request already exists for this player and team.")
        else:
            association = getattr(getattr(request, "user", None), "profile", None)
            association = getattr(association, "association", None)
            if association is None:
                raise forms.ValidationError("Coach must be linked to an association.")
            if association.region_id != region.id:
                raise forms.ValidationError("Coach association is not in this region.")
            if not availability.allowed_associations.filter(id=association.id).exists():
                raise forms.ValidationError("Player has not allowed this association to view availability.")
            if ContactRequest.objects.filter(
                player_id=availability.player_id,
                requesting_association=association,
                status=ContactRequest.Status.PENDING,
            ).exists():
                raise forms.ValidationError("A pending request already exists for this player and association.")

        cleaned_data["_availability"] = availability
        cleaned_data["_region"] = region
        cleaned_data["_association"] = association
        return cleaned_data

    def save(self, *, requested_by):
        availability = self.cleaned_data["_availability"]
        region = self.cleaned_data["_region"]
        team = self.cleaned_data.get("requesting_team")
        association = self.cleaned_data.get("_association")
        message = self.cleaned_data.get("message", "")
        try:
            contact_request = ContactRequest.objects.create(
                player=availability.player,
                requesting_team=team,
                requesting_association=association,
                requested_by=requested_by,
                region=region,
                status=ContactRequest.Status.PENDING,
                message=message,
            )
            send_contact_request_email(self.request, contact_request)
            return contact_request
        except IntegrityError:
            raise forms.ValidationError("A pending request already exists for this player.")


class ContactRequestRespondForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            (ContactRequest.Status.APPROVED, "Approve"),
            (ContactRequest.Status.DECLINED, "Decline"),
        ],
        widget=forms.HiddenInput,
    )
