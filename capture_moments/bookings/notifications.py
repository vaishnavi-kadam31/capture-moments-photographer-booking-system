from django.conf import settings
from django.core.mail import send_mail

from .models import Notification


def notify(user, message, link=""):
    """Save an in-app notification and (if the user has an email) send an email too."""
    Notification.objects.create(user=user, message=message[:255], link=link)
    if user.email:
        send_mail("Capture Moments update", message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
