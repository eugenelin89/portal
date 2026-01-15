from django import forms

from tryouts.models import TryoutEvent


class TryoutEventForm(forms.ModelForm):
    class Meta:
        model = TryoutEvent
        fields = [
            "team",
            "name",
            "start_date",
            "end_date",
            "location",
            "registration_url",
            "notes",
        ]

    def __init__(self, *args, **kwargs):
        team_queryset = kwargs.pop("team_queryset", None)
        super().__init__(*args, **kwargs)
        if team_queryset is not None:
            self.fields["team"].queryset = team_queryset

        for field_name in self.fields:
            field = self.fields[field_name]
            if isinstance(field.widget, (forms.TextInput, forms.URLInput, forms.DateInput)):
                field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("class", "form-control")

        self.fields["start_date"].widget.attrs.setdefault("type", "date")
        self.fields["end_date"].widget.attrs.setdefault("type", "date")

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "End date cannot be earlier than start date.")
        return cleaned_data
