from django.contrib import admin

from .models import Booking, Notification


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "photographer", "event_date", "status", "total_price", "created_at")
    list_filter = ("status", "event_date")
    search_fields = ("client__username", "photographer__user__username", "event_location")
    date_hierarchy = "event_date"
    actions = ["mark_cancelled"]

    @admin.action(description="Cancel selected bookings")
    def mark_cancelled(self, request, queryset):
        queryset.update(status=Booking.CANCELLED)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "is_read", "created_at")
    list_filter = ("is_read",)
