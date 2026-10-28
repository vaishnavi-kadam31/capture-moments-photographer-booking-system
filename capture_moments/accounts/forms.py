from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction

from core.forms import BootstrapFormMixin
from photographers.models import Category, PhotographerProfile

from .models import User


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class _BaseRegistrationForm(BootstrapFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("first_name", "last_name", "email", "phone"):
            self.fields[name].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ClientRegistrationForm(_BaseRegistrationForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.CLIENT
        if commit:
            user.save()
        return user


class PhotographerRegistrationForm(_BaseRegistrationForm):
    city = forms.CharField(max_length=100)
    experience_years = forms.IntegerField(min_value=0, max_value=60, label="Years of experience")
    price_per_hour = forms.DecimalField(min_value=1, max_digits=8, decimal_places=2, label="Price per hour (₹)")
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Photography categories",
    )
    bio = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), label="About you")
    services = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="One service per line, e.g. 'Full-day wedding coverage'.",
    )

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.PHOTOGRAPHER
        user.save()
        profile = PhotographerProfile.objects.create(
            user=user,
            city=self.cleaned_data["city"],
            experience_years=self.cleaned_data["experience_years"],
            price_per_hour=self.cleaned_data["price_per_hour"],
            bio=self.cleaned_data["bio"],
            services=self.cleaned_data["services"],
        )
        profile.categories.set(self.cleaned_data["categories"])
        return user
