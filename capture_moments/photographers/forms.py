from datetime import timedelta

from django import forms
from django.utils import timezone

from accounts.models import User
from core.forms import BootstrapFormMixin

from .models import BlockedDate, Category, PhotographerProfile


class PhotographerFilterForm(BootstrapFormMixin, forms.Form):
    SORT_CHOICES = [
        ("newest", "Newest first"),
        ("price_low", "Price: low to high"),
        ("price_high", "Price: high to low"),
        ("experience", "Most experienced"),
    ]
    q = forms.CharField(required=False, label="Search", widget=forms.TextInput(attrs={"placeholder": "Name or keyword"}))
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, empty_label="All categories")
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "City"}))
    min_price = forms.DecimalField(required=False, min_value=0, label="Min ₹/hr")
    max_price = forms.DecimalField(required=False, min_value=0, label="Max ₹/hr")
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False)

    def clean(self):
        cleaned = super().clean()
        low, high = cleaned.get("min_price"), cleaned.get("max_price")
        if low is not None and high is not None and low > high:
            raise forms.ValidationError("Minimum price cannot be more than maximum price.")
        return cleaned


class UserBasicsForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Another account already uses this email.")
        return email


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(queryset=Category.objects.all(), widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = PhotographerProfile
        fields = ("profile_photo", "categories", "bio", "services", "experience_years", "city", "price_per_hour", "is_active_listing")
        widgets = {"bio": forms.Textarea(attrs={"rows": 4}), "services": forms.Textarea(attrs={"rows": 4})}
        labels = {"price_per_hour": "Price per hour (₹)", "experience_years": "Years of experience"}


class BlockedDateForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = BlockedDate
        fields = ("date", "reason")
        widgets = {"date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, profile, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)
        self.fields["date"].widget.attrs["min"] = (timezone.localdate() + timedelta(days=1)).isoformat()

    def clean_date(self):
        d = self.cleaned_data["date"]
        if d <= timezone.localdate():
            raise forms.ValidationError("Choose a date from tomorrow onwards.")
        if BlockedDate.objects.filter(profile=self.profile, date=d).exists():
            raise forms.ValidationError("This date is already blocked.")
        # Local import avoids a circular import (bookings imports photographers)
        from bookings.models import Booking

        if Booking.objects.filter(photographer=self.profile, event_date=d, status=Booking.ACCEPTED).exists():
            raise forms.ValidationError("You already have an accepted booking on this date.")
        return d
