from django import forms
from django.utils import timezone

from availability.models import PlayerAvailability
from organizations.models import Team


POSITION_CHOICES = [
    ("P", "Pitcher"),
    ("C", "Catcher"),
    ("1B", "First Base"),
    ("2B", "Second Base"),
    ("3B", "Third Base"),
    ("SS", "Shortstop"),
    ("OF", "Outfield"),
    ("IF", "Infield"),
    ("UTL", "Utility"),
]

LEVEL_CHOICES = [
    ("AAA", "AAA"),
    ("AA", "AA"),
    ("A", "A"),
    ("B", "B"),
    ("C", "C"),
]


class PlayerAvailabilityForm(forms.ModelForm):
    positions = forms.MultipleChoiceField(
        choices=POSITION_CHOICES,
        required=False,
        widget=forms.SelectMultiple,
    )
    levels = forms.MultipleChoiceField(
        choices=LEVEL_CHOICES,
        required=False,
        widget=forms.SelectMultiple,
    )
    allowed_teams = forms.ModelMultipleChoiceField(
        queryset=Team.objects.none(),
        required=False,
        widget=forms.SelectMultiple,
        help_text="Only these teams can view your availability.",
    )

    class Meta:
        model = PlayerAvailability
        fields = ("is_open", "positions", "levels", "expires_at", "allowed_teams")
        widgets = {
            "expires_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        region = kwargs.pop("region", None)
        super().__init__(*args, **kwargs)
        if region is not None:
            self.fields["allowed_teams"].queryset = Team.objects.filter(region=region).order_by("name")

        for field_name in self.fields:
            field = self.fields[field_name]
            if isinstance(field.widget, (forms.TextInput, forms.DateTimeInput)):
                field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.setdefault("class", "form-select")
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")

    def clean_positions(self):
        positions = self.cleaned_data.get("positions")
        if not positions:
            return []
        return positions

    def clean_levels(self):
        levels = self.cleaned_data.get("levels")
        if not levels:
            return []
        return levels

    def clean_expires_at(self):
        expires_at = self.cleaned_data.get("expires_at")
        if expires_at and expires_at <= timezone.now():
            raise forms.ValidationError("Expiry must be in the future.")
        return expires_at
