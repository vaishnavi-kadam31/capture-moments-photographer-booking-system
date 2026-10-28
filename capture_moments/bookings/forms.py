from datetime import timedelta

from django import forms
from django.utils import timezone

from core.forms import BootstrapFormMixin

from .availability import date_status
from .models import Booking


class BookingForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["event_type", "event_date", "start_time", "duration_hours", "event_location", "message"]
        widgets = {
            "event_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "start_time": forms.TimeInput(
                attrs={
                    "type": "text",
                    "data-time-picker": "",
                    "inputmode": "text",
                    "autocomplete": "off",
                    "placeholder": "HH:MM",
                },
                format="%H:%M",
            ),
            "duration_hours": forms.NumberInput(attrs={"min": 1, "max": 12}),
            "message": forms.Textarea(attrs={"rows": 3, "placeholder": "Tell the photographer about your event..."}),
        }
        labels = {"event_type": "Type of shoot", "event_location": "Event location", "message": "Message (optional)"}

    def __init__(self, *args, photographer, client, **kwargs):
        self.photographer = photographer
        self.client = client
        super().__init__(*args, **kwargs)
        categories = photographer.categories.all()
        self.fields["event_type"].queryset = categories
        self.fields["event_type"].empty_label = "Select..."
        self.fields["event_type"].required = categories.exists()
        self.fields["event_date"].widget.attrs["min"] = (timezone.localdate() + timedelta(days=1)).isoformat()

    def clean_event_date(self):
        d = self.cleaned_data["event_date"]
        today = timezone.localdate()
        if d <= today:
            raise forms.ValidationError("Please choose a date from tomorrow onwards.")
        if d > today + timedelta(days=365):
            raise forms.ValidationError("Bookings can be made up to one year in advance.")
        return d

    def clean(self):
        cleaned = super().clean()
        d = cleaned.get("event_date")
        if d:
            status = date_status(self.photographer, d)
            if status == "blocked":
                self.add_error("event_date", "The photographer is not available on this date.")
            elif status == "booked":
                self.add_error("event_date", "The photographer is already booked on this date.")
            elif Booking.objects.filter(
                client=self.client,
                photographer=self.photographer,
                event_date=d,
                status__in=[Booking.PENDING, Booking.ACCEPTED],
            ).exists():
                self.add_error("event_date", "You already have an active request with this photographer for this date.")
        return cleaned

    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.client = self.client
        booking.photographer = self.photographer
        booking.total_price = self.photographer.price_per_hour * booking.duration_hours
        booking.status = Booking.PENDING
        if commit:
            booking.save()
        return booking
