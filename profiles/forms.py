from django import forms

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

    class Meta:
        model = PlayerProfile
        fields = ("display_name", "birth_year", "positions", "bats", "throws")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            field = self.fields[field_name]
            if isinstance(field.widget, (forms.TextInput, forms.NumberInput, forms.Select, forms.SelectMultiple)):
                field.widget.attrs.setdefault("class", "form-control")
        self.fields["positions"].widget.attrs["class"] = "form-select"
        self.fields["bats"].widget.attrs["class"] = "form-select"
        self.fields["throws"].widget.attrs["class"] = "form-select"

    def clean_positions(self):
        positions = self.cleaned_data.get("positions")
        if not positions:
            return []
        return positions
