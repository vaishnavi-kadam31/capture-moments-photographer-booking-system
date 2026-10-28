"""
Automated tests. Run them with:   python manage.py test
Each test sends fake requests to the app (no browser needed) and checks the result.
"""
from datetime import time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from bookings.models import Booking, Notification
from core.management.commands.seed_data import make_image
from photographers.models import BlockedDate, Category, PhotographerProfile

PASSWORD = "Str0ng!Pass#123"


def future(days=10):
    return timezone.localdate() + timedelta(days=days)


class BaseCase(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Wedding")
        self.cli = User.objects.create_user("cli", "cli@example.com", PASSWORD, first_name="Cara", last_name="Client", role=User.CLIENT)
        self.pho = User.objects.create_user("pho", "pho@example.com", PASSWORD, first_name="Paul", last_name="Photo", role=User.PHOTOGRAPHER)
        self.profile = PhotographerProfile.objects.create(
            user=self.pho, bio="Bio", services="Weddings\nPortraits", experience_years=3, city="Nashik", price_per_hour=1000
        )
        self.profile.categories.add(self.cat)

    def booking_data(self, **overrides):
        data = {
            "event_type": self.cat.pk, "event_date": future().isoformat(), "start_time": "10:00",
            "duration_hours": 4, "event_location": "Grand Hall", "message": "Hello",
        }
        data.update(overrides)
        return data

    def make_booking(self, client=None, date=None, status=Booking.PENDING):
        return Booking.objects.create(
            client=client or self.cli, photographer=self.profile, event_type=self.cat,
            event_date=date or future(), start_time="10:00", duration_hours=2,
            event_location="X", total_price=2000, status=status,
        )


class RegistrationAndAuthTests(BaseCase):
    def test_client_registration_creates_client(self):
        resp = self.client.post(reverse("accounts:register_client"), {
            "username": "newclient", "first_name": "N", "last_name": "C", "email": "n@example.com",
            "phone": "9876543210", "password1": PASSWORD, "password2": PASSWORD,
        })
        self.assertEqual(resp.status_code, 302)
        user = User.objects.get(username="newclient")
        self.assertEqual(user.role, User.CLIENT)

    def test_photographer_registration_creates_profile(self):
        resp = self.client.post(reverse("accounts:register_photographer"), {
            "username": "newph", "first_name": "N", "last_name": "P", "email": "np@example.com",
            "phone": "9876543211", "password1": PASSWORD, "password2": PASSWORD, "city": "Pune",
            "experience_years": 4, "price_per_hour": "1500", "categories": [self.cat.pk],
            "bio": "I shoot.", "services": "Weddings",
        })
        self.assertEqual(resp.status_code, 302)
        user = User.objects.get(username="newph")
        self.assertEqual(user.role, User.PHOTOGRAPHER)
        self.assertEqual(user.photographer_profile.city, "Pune")
        self.assertEqual(user.photographer_profile.categories.count(), 1)

    def test_duplicate_email_rejected(self):
        resp = self.client.post(reverse("accounts:register_client"), {
            "username": "other", "first_name": "O", "last_name": "T", "email": "CLI@example.com",
            "phone": "9876543210", "password1": PASSWORD, "password2": PASSWORD,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="other").exists())

    def test_login_redirects_by_role(self):
        self.client.login(username="cli", password=PASSWORD)
        self.assertRedirects(self.client.get(reverse("accounts:dashboard")), reverse("bookings:client_dashboard"))
        self.client.logout()
        self.client.login(username="pho", password=PASSWORD)
        self.assertRedirects(self.client.get(reverse("accounts:dashboard")), reverse("bookings:photographer_dashboard"))

    def test_anonymous_redirected_to_login(self):
        resp = self.client.get(reverse("bookings:client_dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp["Location"])

    def test_role_protection(self):
        self.client.login(username="pho", password=PASSWORD)
        resp = self.client.get(reverse("bookings:client_dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.client.logout()
        self.client.login(username="cli", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("bookings:photographer_dashboard")).status_code, 302)


class PublicPageTests(BaseCase):
    def test_home_list_and_detail_load(self):
        self.assertEqual(self.client.get(reverse("core:home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("photographers:list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("photographers:detail", args=[self.profile.pk])).status_code, 200)

    def test_search_filters(self):
        other_user = User.objects.create_user("pho2", "pho2@example.com", PASSWORD, role=User.PHOTOGRAPHER)
        other = PhotographerProfile.objects.create(
            user=other_user, bio="b", services="s", experience_years=9, city="Pune", price_per_hour=5000
        )
        portrait = Category.objects.create(name="Portrait")
        other.categories.add(portrait)
        url = reverse("photographers:list")

        resp = self.client.get(url, {"city": "pune"})
        self.assertEqual([p.pk for p in resp.context["page_obj"]], [other.pk])
        resp = self.client.get(url, {"category": self.cat.pk})
        self.assertEqual([p.pk for p in resp.context["page_obj"]], [self.profile.pk])
        resp = self.client.get(url, {"min_price": 2000})
        self.assertEqual([p.pk for p in resp.context["page_obj"]], [other.pk])
        resp = self.client.get(url, {"max_price": 2000})
        self.assertEqual([p.pk for p in resp.context["page_obj"]], [self.profile.pk])
        resp = self.client.get(url, {"sort": "price_high"})
        self.assertEqual([p.pk for p in resp.context["page_obj"]], [other.pk, self.profile.pk])

    def test_hidden_listing_not_shown(self):
        self.profile.is_active_listing = False
        self.profile.save()
        resp = self.client.get(reverse("photographers:list"))
        self.assertEqual(len(resp.context["page_obj"]), 0)
        self.assertEqual(self.client.get(reverse("photographers:detail", args=[self.profile.pk])).status_code, 404)


class DemoImageTests(TestCase):
    def test_make_image_has_filename(self):
        image = make_image(((10, 20, 30), (200, 220, 240)), "Sample")
        self.assertIsNotNone(image.name)
        self.assertTrue(image.name.endswith(".jpg"))
        self.assertGreater(len(image.read()), 0)


class BookingFlowTests(BaseCase):
    def test_client_can_create_booking(self):
        self.client.login(username="cli", password=PASSWORD)
        resp = self.client.post(reverse("bookings:create", args=[self.profile.pk]), self.booking_data())
        self.assertRedirects(resp, reverse("bookings:client_dashboard"))
        booking = Booking.objects.get()
        self.assertEqual(booking.status, Booking.PENDING)
        self.assertEqual(booking.total_price, 4000)
        self.assertTrue(Notification.objects.filter(user=self.pho).exists())

    def test_picker_time_is_stored_and_displayed_in_existing_formats(self):
        self.client.force_login(self.cli)
        response = self.client.get(reverse("bookings:create", args=[self.profile.pk]))
        self.assertContains(response, 'type="text"')
        self.assertContains(response, 'data-time-picker=""')

        self.client.post(
            reverse("bookings:create", args=[self.profile.pk]),
            self.booking_data(start_time="14:30"),
        )
        booking = Booking.objects.get()
        self.assertEqual(booking.start_time, time(14, 30))
        response = self.client.get(reverse("bookings:client_dashboard"))
        self.assertContains(response, "02:30 PM")

    def test_past_date_rejected(self):
        self.client.login(username="cli", password=PASSWORD)
        past = (timezone.localdate() - timedelta(days=2)).isoformat()
        resp = self.client.post(reverse("bookings:create", args=[self.profile.pk]), self.booking_data(event_date=past))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Booking.objects.count(), 0)

    def test_invalid_duration_rejected(self):
        self.client.login(username="cli", password=PASSWORD)
        for hours in (0, 13):
            self.client.post(reverse("bookings:create", args=[self.profile.pk]), self.booking_data(duration_hours=hours))
        self.assertEqual(Booking.objects.count(), 0)

    def test_blocked_date_rejected(self):
        BlockedDate.objects.create(profile=self.profile, date=future())
        self.client.login(username="cli", password=PASSWORD)
        self.client.post(reverse("bookings:create", args=[self.profile.pk]), self.booking_data())
        self.assertEqual(Booking.objects.count(), 0)

    def test_duplicate_active_request_rejected(self):
        self.make_booking()
        self.client.login(username="cli", password=PASSWORD)
        self.client.post(reverse("bookings:create", args=[self.profile.pk]), self.booking_data())
        self.assertEqual(Booking.objects.count(), 1)

    def test_photographer_cannot_book(self):
        self.client.login(username="pho", password=PASSWORD)
        resp = self.client.post(reverse("bookings:create", args=[self.profile.pk]), self.booking_data())
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Booking.objects.count(), 0)

    def test_accept_updates_status_notifies_and_blocks_date(self):
        booking = self.make_booking()
        self.client.login(username="pho", password=PASSWORD)
        self.client.post(reverse("bookings:respond", args=[booking.pk, "accept"]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.ACCEPTED)
        self.assertTrue(Notification.objects.filter(user=self.cli, message__icontains="accepted").exists())

        # Another client now cannot book the same date
        other = User.objects.create_user("cli2", "cli2@example.com", PASSWORD, role=User.CLIENT)
        self.client.logout()
        self.client.login(username="cli2", password=PASSWORD)
        self.client.post(reverse("bookings:create", args=[self.profile.pk]), self.booking_data())
        self.assertEqual(Booking.objects.filter(client=other).count(), 0)

    def test_cannot_accept_two_requests_for_same_date(self):
        other = User.objects.create_user("cli2", "cli2@example.com", PASSWORD, role=User.CLIENT)
        first, second = self.make_booking(), self.make_booking(client=other)
        self.client.login(username="pho", password=PASSWORD)
        self.client.post(reverse("bookings:respond", args=[first.pk, "accept"]))
        self.client.post(reverse("bookings:respond", args=[second.pk, "accept"]))
        first.refresh_from_db(); second.refresh_from_db()
        self.assertEqual(first.status, Booking.ACCEPTED)
        self.assertEqual(second.status, Booking.PENDING)

    def test_reject(self):
        booking = self.make_booking()
        self.client.login(username="pho", password=PASSWORD)
        self.client.post(reverse("bookings:respond", args=[booking.pk, "reject"]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.REJECTED)

    def test_other_photographer_cannot_respond(self):
        booking = self.make_booking()
        other_user = User.objects.create_user("pho2", "pho2@example.com", PASSWORD, role=User.PHOTOGRAPHER)
        PhotographerProfile.objects.create(user=other_user, bio="b", services="s", experience_years=1, city="X", price_per_hour=1)
        self.client.login(username="pho2", password=PASSWORD)
        resp = self.client.post(reverse("bookings:respond", args=[booking.pk, "accept"]))
        self.assertEqual(resp.status_code, 404)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.PENDING)

    def test_get_request_cannot_change_status(self):
        booking = self.make_booking()
        self.client.login(username="pho", password=PASSWORD)
        resp = self.client.get(reverse("bookings:respond", args=[booking.pk, "accept"]))
        self.assertEqual(resp.status_code, 405)

    def test_client_can_cancel_and_photographer_is_notified(self):
        booking = self.make_booking()
        self.client.login(username="cli", password=PASSWORD)
        self.client.post(reverse("bookings:cancel", args=[booking.pk]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.CANCELLED)
        self.assertTrue(Notification.objects.filter(user=self.pho, message__icontains="cancelled").exists())

    def test_client_cannot_cancel_someone_elses_booking(self):
        other = User.objects.create_user("cli2", "cli2@example.com", PASSWORD, role=User.CLIENT)
        booking = self.make_booking(client=other)
        self.client.login(username="cli", password=PASSWORD)
        self.assertEqual(self.client.post(reverse("bookings:cancel", args=[booking.pk])).status_code, 404)

    def test_dashboards_and_calendar_render(self):
        self.make_booking(status=Booking.ACCEPTED)
        self.client.login(username="cli", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("bookings:client_dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("bookings:client_dashboard"), {"status": "accepted"}).status_code, 200)
        self.assertEqual(self.client.get(reverse("bookings:create", args=[self.profile.pk])).status_code, 200)
        self.client.logout()
        self.client.login(username="pho", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("bookings:photographer_dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("photographers:manage_availability")).status_code, 200)
        self.assertEqual(self.client.get(reverse("photographers:manage_portfolio")).status_code, 200)
        self.assertEqual(self.client.get(reverse("photographers:manage_profile")).status_code, 200)
        self.assertEqual(self.client.get(reverse("photographers:detail", args=[self.profile.pk]), {"month": "garbage"}).status_code, 200)

    def test_notifications_marked_read_after_viewing(self):
        Notification.objects.create(user=self.cli, message="Hi")
        self.client.login(username="cli", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("core:home")).context["unread_count"], 1)
        self.client.get(reverse("bookings:notifications"))
        self.assertEqual(self.client.get(reverse("core:home")).context["unread_count"], 0)


class AvailabilityTests(BaseCase):
    def test_photographer_can_block_and_unblock_date(self):
        self.client.login(username="pho", password=PASSWORD)
        self.client.post(reverse("photographers:manage_availability"), {"date": future(20).isoformat(), "reason": "Trip"})
        blocked = BlockedDate.objects.get()
        self.client.post(reverse("photographers:remove_blocked_date", args=[blocked.pk]))
        self.assertEqual(BlockedDate.objects.count(), 0)

    def test_cannot_block_date_with_accepted_booking(self):
        self.make_booking(status=Booking.ACCEPTED, date=future(15))
        self.client.login(username="pho", password=PASSWORD)
        self.client.post(reverse("photographers:manage_availability"), {"date": future(15).isoformat(), "reason": ""})
        self.assertEqual(BlockedDate.objects.count(), 0)


class AdminDashboardTests(BaseCase):
    def test_only_staff_can_open(self):
        self.client.login(username="cli", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("core:admin_dashboard")).status_code, 302)
        User.objects.create_user("boss", "boss@example.com", PASSWORD, is_staff=True)
        self.client.logout()
        self.client.login(username="boss", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("core:admin_dashboard")).status_code, 200)

    def test_staff_can_deactivate_user_and_cancel_booking(self):
        booking = self.make_booking()
        User.objects.create_user("boss", "boss@example.com", PASSWORD, is_staff=True)
        self.client.login(username="boss", password=PASSWORD)
        self.client.post(reverse("core:toggle_user", args=[self.cli.pk]))
        self.cli.refresh_from_db()
        self.assertFalse(self.cli.is_active)
        self.client.post(reverse("core:admin_cancel_booking", args=[booking.pk]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.CANCELLED)
