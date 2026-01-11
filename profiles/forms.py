from django import forms

from organizations.models import Association
from profiles.models import PlayerProfile


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


class PlayerProfileForm(forms.ModelForm):
    positions = forms.MultipleChoiceField(
        choices=POSITION_CHOICES,
        required=False,
        widget=forms.SelectMultiple,
    )
    current_association = forms.ModelChoiceField(
        queryset=Association.objects.none(),
        required=False,
    )
    visible_associations = forms.ModelMultipleChoiceField(
        queryset=Association.objects.none(),
        required=False,
        widget=forms.SelectMultiple,
    )

    class Meta:
        model = PlayerProfile
        fields = (
            "display_name",
            "birth_year",
            "positions",
            "bats",
            "throws",
            "current_association",
            "profile_visibility",
            "visible_associations",
            "pbr_url",
            "pg_url",
            "youtube_url",
            "instagram_handle",
            "twitter_handle",
            "bio",
        )
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        region = kwargs.pop("region", None)
        super().__init__(*args, **kwargs)
        if region is not None:
            associations = Association.objects.filter(region=region, is_active=True).order_by("name")
            self.fields["current_association"].queryset = associations
            self.fields["visible_associations"].queryset = associations

        for field_name in self.fields:
            field = self.fields[field_name]
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.EmailInput)):
                field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.setdefault("class", "form-select")
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("class", "form-control")

        self.fields["positions"].widget.attrs["class"] = "form-select"
        self.fields["bats"].widget.attrs["class"] = "form-select"
        self.fields["throws"].widget.attrs["class"] = "form-select"
        self.fields["profile_visibility"].widget.attrs["class"] = "form-select"

    def clean_positions(self):
        positions = self.cleaned_data.get("positions")
        if not positions:
            return []
        return positions

    def clean(self):
        cleaned_data = super().clean()
        visibility = cleaned_data.get("profile_visibility")
        visible_associations = cleaned_data.get("visible_associations")
        if visibility == PlayerProfile.Visibility.SPECIFIC and not visible_associations:
            self.add_error("visible_associations", "Select at least one association or change the visibility setting.")
        if visibility in (PlayerProfile.Visibility.ALL, PlayerProfile.Visibility.NONE):
            cleaned_data["visible_associations"] = Association.objects.none()
        return cleaned_data
