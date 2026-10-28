from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import ClientRegistrationForm, LoginForm, PhotographerRegistrationForm
from .models import User


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


def register_client(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = ClientRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome to Capture Moments! Your account is ready.")
        return redirect("accounts:dashboard")
    return render(request, "accounts/register_client.html", {"form": form})


def register_photographer(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = PhotographerRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your photographer account is ready. Upload your portfolio next!")
        return redirect("photographers:manage_portfolio")
    return render(request, "accounts/register_photographer.html", {"form": form})


@login_required
def dashboard(request):
    """Send each kind of user to their own dashboard."""
    user = request.user
    if user.is_staff:
        return redirect("core:admin_dashboard")
    if user.role == User.PHOTOGRAPHER:
        return redirect("bookings:photographer_dashboard")
    return redirect("bookings:client_dashboard")
