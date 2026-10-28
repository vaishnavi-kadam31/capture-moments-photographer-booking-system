from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from photographers.models import Category, PhotographerProfile


class Booking(models.Model):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (ACCEPTED, "Accepted"),
        (REJECTED, "Rejected"),
        (CANCELLED, "Cancelled"),
    ]

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    photographer = models.ForeignKey(PhotographerProfile, on_delete=models.CASCADE, related_name="bookings")
    event_type = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings")
    event_date = models.DateField()
    start_time = models.TimeField()
    duration_hours = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    event_location = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking #{self.pk}: {self.client} -> {self.photographer.display_name} on {self.event_date}"

    @property
    def badge_class(self):
        return {
            self.PENDING: "warning text-dark",
            self.ACCEPTED: "success",
            self.REJECTED: "danger",
            self.CANCELLED: "secondary",
        }[self.status]


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"To {self.user}: {self.message[:40]}"
