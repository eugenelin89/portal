from django import forms
from django.contrib.auth import get_user_model

from organizations.models import Association


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
