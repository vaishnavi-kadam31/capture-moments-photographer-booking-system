from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.models import User
from bookings.models import Booking
from bookings.notifications import notify
from photographers.models import Category, PhotographerProfile


def home(request):
    featured = (
        PhotographerProfile.objects.filter(is_active_listing=True, user__is_active=True)
        .select_related("user").prefetch_related("categories")[:6]
    )
    context = {
        "featured": featured,
        "categories": Category.objects.all(),
        "photographer_count": PhotographerProfile.objects.filter(is_active_listing=True).count(),
        "booking_count": Booking.objects.filter(status=Booking.ACCEPTED).count(),
    }
    return render(request, "core/home.html", context)


@staff_member_required(login_url="accounts:login")
def admin_dashboard(request):
    bookings = Booking.objects.select_related("client", "photographer__user")
    context = {
        "client_count": User.objects.filter(role=User.CLIENT, is_staff=False).count(),
        "photographer_count": PhotographerProfile.objects.count(),
        "booking_total": bookings.count(),
        "status_counts": [(label, bookings.filter(status=value).count(), value) for value, label in Booking.STATUS_CHOICES],
        "clients": User.objects.filter(role=User.CLIENT, is_staff=False).order_by("-date_joined")[:50],
        "photographers": PhotographerProfile.objects.select_related("user").order_by("-created_at")[:50],
        "bookings": bookings[:50],
    }
    return render(request, "core/admin_dashboard.html", context)


@staff_member_required(login_url="accounts:login")
@require_POST
def toggle_user_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.is_staff or user.pk == request.user.pk:
        messages.error(request, "You can't deactivate staff accounts from here.")
    else:
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        messages.success(request, f"{user.display_name} is now {'active' if user.is_active else 'deactivated'}.")
    return redirect("core:admin_dashboard")


@staff_member_required(login_url="accounts:login")
@require_POST
def admin_cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if booking.status in (Booking.PENDING, Booking.ACCEPTED):
        booking.status = Booking.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        text = f"An administrator cancelled the booking for {booking.event_date:%d %b %Y}."
        notify(booking.client, text, reverse("bookings:client_dashboard"))
        notify(booking.photographer.user, text, reverse("bookings:photographer_dashboard"))
        messages.success(request, f"Booking #{booking.pk} cancelled.")
    else:
        messages.error(request, "Only pending or accepted bookings can be cancelled.")
    return redirect("core:admin_dashboard")
