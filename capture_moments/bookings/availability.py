"""Everything about 'is this photographer free on this day?' lives here."""
import calendar
from datetime import date

from django.utils import timezone

from photographers.models import BlockedDate

from .models import Booking


def date_status(profile, d):
    """Return 'past', 'blocked', 'booked' or 'available' for one date."""
    if d <= timezone.localdate():
        return "past"
    if BlockedDate.objects.filter(profile=profile, date=d).exists():
        return "blocked"
    if Booking.objects.filter(photographer=profile, event_date=d, status=Booking.ACCEPTED).exists():
        return "booked"
    return "available"


def parse_month(value):
    """Turn '2026-11' into (2026, 11). Bad input -> current month. Clamped to the next 12 months."""
    today = timezone.localdate()
    year, month = today.year, today.month
    if value:
        try:
            y, m = value.split("-")
            y, m = int(y), int(m)
            date(y, m, 1)
        except (ValueError, TypeError):
            pass
        else:
            year, month = y, m
    low = today.year * 12 + today.month - 1
    index = max(low, min(low + 12, year * 12 + month - 1))
    year, month = divmod(index, 12)
    return year, month + 1


def build_month_calendar(profile, year, month):
    today = timezone.localdate()
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])

    blocked = set(BlockedDate.objects.filter(profile=profile, date__range=(first, last)).values_list("date", flat=True))
    booked = set(
        Booking.objects.filter(photographer=profile, status=Booking.ACCEPTED, event_date__range=(first, last))
        .values_list("event_date", flat=True)
    )

    weeks = []
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(year, month):
        row = []
        for d in week:
            if d.month != month:
                row.append(None)
            elif d <= today:
                row.append({"day": d.day, "status": "past"})
            elif d in blocked:
                row.append({"day": d.day, "status": "blocked"})
            elif d in booked:
                row.append({"day": d.day, "status": "booked"})
            else:
                row.append({"day": d.day, "status": "available"})
        weeks.append(row)

    low = today.year * 12 + today.month - 1
    index = year * 12 + month - 1

    def label(i):
        y, m = divmod(i, 12)
        return f"{y}-{m + 1:02d}"

    return {
        "title": f"{calendar.month_name[month]} {year}",
        "weeks": weeks,
        "prev": label(index - 1) if index > low else None,
        "next": label(index + 1) if index < low + 12 else None,
    }
