from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(role):
    """Only let logged-in users with the given role ('client' or 'photographer') in."""

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.role != role:
                messages.error(request, "You don't have permission to open that page.")
                return redirect("accounts:dashboard")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
