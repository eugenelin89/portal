from django import forms
from django.contrib.auth import get_user_model

from organizations.models import Association
from profiles.models import PlayerProfile


class CoachSignupForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    association = forms.ModelChoiceField(queryset=Association.objects.none())
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        region = kwargs.pop("region", None)
        super().__init__(*args, **kwargs)
        if region is not None:
            self.fields["association"].queryset = Association.objects.filter(
                region=region,
                is_active=True,
            ).order_by("name")

        for field_name in self.fields:
            field = self.fields[field_name]
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput)):
                field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        if password and confirm and password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned_data


class PlayerSignupForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    birth_year = forms.IntegerField(min_value=1900, max_value=2100)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=30)
    current_association = forms.ModelChoiceField(
        queryset=Association.objects.none(),
        required=False,
    )
    available_for_transfer = forms.BooleanField(required=False)
    profile_visibility = forms.ChoiceField(choices=PlayerProfile.Visibility.choices)
    visible_associations = forms.ModelMultipleChoiceField(
        queryset=Association.objects.none(),
        required=False,
        widget=forms.SelectMultiple,
    )
    pbr_url = forms.URLField(required=False)
    pg_url = forms.URLField(required=False)
    youtube_url = forms.URLField(required=False)
    instagram_handle = forms.CharField(max_length=80, required=False)
    twitter_handle = forms.CharField(max_length=80, required=False)
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}))
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        region = kwargs.pop("region", None)
        super().__init__(*args, **kwargs)
        if region is not None:
            associations = Association.objects.filter(region=region, is_active=True).order_by("name")
            self.fields["current_association"].queryset = associations
            self.fields["visible_associations"].queryset = associations

        self.fields["profile_visibility"].initial = PlayerProfile.Visibility.NONE
        self.fields["profile_visibility"].help_text = (
            "Choose which associations can view your profile."
        )
        self.fields["visible_associations"].help_text = (
            "Select specific associations if you chose the specific option."
        )

        for field_name in self.fields:
            field = self.fields[field_name]
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.NumberInput)):
                field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.setdefault("class", "form-select")
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("class", "form-control")
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        visibility = cleaned_data.get("profile_visibility")
        visible_associations = cleaned_data.get("visible_associations")
        if password and confirm and password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        if visibility == PlayerProfile.Visibility.SPECIFIC and not visible_associations:
            self.add_error("visible_associations", "Select at least one association or change the visibility setting.")
        return cleaned_data


class PlayerContactForm(forms.Form):
    phone_number = forms.CharField(max_length=30, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            field = self.fields[field_name]
            if isinstance(field.widget, forms.TextInput):
                field.widget.attrs.setdefault("class", "form-control")
