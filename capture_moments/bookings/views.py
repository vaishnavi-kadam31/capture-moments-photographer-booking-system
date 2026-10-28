from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from core.decorators import role_required
from photographers.models import BlockedDate, PhotographerProfile

from .availability import build_month_calendar, parse_month
from .forms import BookingForm
from .models import Booking, Notification
from .notifications import notify


# ------------------------------------------------------------- client side
@role_required(User.CLIENT)
def create_booking(request, photographer_id):
    profile = get_object_or_404(
        PhotographerProfile.objects.select_related("user"),
        pk=photographer_id, is_active_listing=True, user__is_active=True,
    )
    form = BookingForm(request.POST or None, photographer=profile, client=request.user)
    if request.method == "POST" and form.is_valid():
        booking = form.save()
        notify(
            profile.user,
            f"New booking request from {request.user.display_name} for {booking.event_date:%d %b %Y}.",
            reverse("bookings:photographer_dashboard"),
        )
        messages.success(request, "Booking request sent! You'll be notified when the photographer responds.")
        return redirect("bookings:client_dashboard")
    year, month = parse_month(request.GET.get("month"))
    return render(
        request,
        "bookings/booking_form.html",
        {"form": form, "profile": profile, "calendar": build_month_calendar(profile, year, month)},
    )


@role_required(User.CLIENT)
def client_dashboard(request):
    all_bookings = Booking.objects.filter(client=request.user).select_related("photographer__user", "event_type")
    status = request.GET.get("status", "")
    valid = {s for s, _ in Booking.STATUS_CHOICES}
    bookings = all_bookings.filter(status=status) if status in valid else all_bookings
    counts = {s: all_bookings.filter(status=s).count() for s in valid}
    return render(
        request,
        "bookings/client_dashboard.html",
        {
            "bookings": bookings,
            "status": status if status in valid else "",
            "counts": counts,
            "total": all_bookings.count(),
            "status_choices": Booking.STATUS_CHOICES,
            "today": timezone.localdate(),
        },
    )


@role_required(User.CLIENT)
@require_POST
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, client=request.user)
    if booking.status not in (Booking.PENDING, Booking.ACCEPTED) or booking.event_date <= timezone.localdate():
        messages.error(request, "This booking can no longer be cancelled.")
        return redirect("bookings:client_dashboard")
    booking.status = Booking.CANCELLED
    booking.save(update_fields=["status", "updated_at"])
    notify(
        booking.photographer.user,
        f"{request.user.display_name} cancelled the booking for {booking.event_date:%d %b %Y}.",
        reverse("bookings:photographer_dashboard"),
    )
    messages.success(request, "Booking cancelled.")
    return redirect("bookings:client_dashboard")


# ------------------------------------------------------- photographer side
@role_required(User.PHOTOGRAPHER)
def photographer_dashboard(request):
    profile = get_object_or_404(PhotographerProfile, user=request.user)
    bookings = list(profile.bookings.select_related("client", "event_type"))
    today = timezone.localdate()
    context = {
        "profile": profile,
        "pending": [b for b in bookings if b.status == Booking.PENDING],
        "upcoming": sorted(
            [b for b in bookings if b.status == Booking.ACCEPTED and b.event_date > today], key=lambda b: b.event_date
        ),
        "history": [
            b for b in bookings
            if b.status in (Booking.REJECTED, Booking.CANCELLED) or (b.status == Booking.ACCEPTED and b.event_date <= today)
        ],
        "total": len(bookings),
        "accepted_count": sum(b.status == Booking.ACCEPTED for b in bookings),
        "portfolio_count": profile.portfolio.count(),
    }
    return render(request, "bookings/photographer_dashboard.html", context)


@role_required(User.PHOTOGRAPHER)
@require_POST
def respond_booking(request, pk, action):
    if action not in ("accept", "reject"):
        raise Http404
    profile = get_object_or_404(PhotographerProfile, user=request.user)
    with transaction.atomic():
        booking = get_object_or_404(Booking.objects.select_for_update(), pk=pk, photographer=profile)
        if booking.status != Booking.PENDING:
            messages.warning(request, "This request has already been handled.")
            return redirect("bookings:photographer_dashboard")
        if action == "accept":
            clash = Booking.objects.filter(
                photographer=profile, event_date=booking.event_date, status=Booking.ACCEPTED
            ).exclude(pk=booking.pk).exists()
            blocked = BlockedDate.objects.filter(profile=profile, date=booking.event_date).exists()
            if clash or blocked:
                messages.error(request, "You can't accept this: that date is already booked or blocked.")
                return redirect("bookings:photographer_dashboard")
            booking.status = Booking.ACCEPTED
        else:
            booking.status = Booking.REJECTED
        booking.save(update_fields=["status", "updated_at"])

    word = "accepted" if action == "accept" else "declined"
    notify(
        booking.client,
        f"{profile.display_name} {word} your booking request for {booking.event_date:%d %b %Y}.",
        reverse("bookings:client_dashboard"),
    )
    messages.success(request, f"Booking {word}.")
    return redirect("bookings:photographer_dashboard")


# ------------------------------------------------------------ notifications
def notifications_list(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    items = list(Notification.objects.filter(user=request.user)[:50])
    # Opening the page marks everything as read (items already loaded keep their old state for display)
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, "bookings/notifications.html", {"items": items})
