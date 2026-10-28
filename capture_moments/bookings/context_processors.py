from .models import Notification


def notifications(request):
    """Makes `unread_count` available in every template (for the navbar bell)."""
    if request.user.is_authenticated:
        return {"unread_count": Notification.objects.filter(user=request.user, is_read=False).count()}
    return {"unread_count": 0}
