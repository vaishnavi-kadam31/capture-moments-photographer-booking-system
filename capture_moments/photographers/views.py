from django.contrib import messages
from django.core.paginator import Paginator
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import User
from bookings.availability import build_month_calendar, parse_month
from core.decorators import role_required

from .forms import BlockedDateForm, PhotographerFilterForm, ProfileForm, UserBasicsForm
from .models import BlockedDate, PhotographerProfile, PortfolioImage
from .validators import validate_image_size

MAX_PORTFOLIO_IMAGES = 30
MAX_UPLOADS_AT_ONCE = 10


def _visible_profiles():
    return PhotographerProfile.objects.filter(is_active_listing=True, user__is_active=True).select_related("user")


def photographer_list(request):
    form = PhotographerFilterForm(request.GET)
    profiles = _visible_profiles().prefetch_related("categories")
    sort = "newest"

    if form.is_valid():
        data = form.cleaned_data
        if data["q"]:
            q = data["q"].strip()
            profiles = profiles.filter(
                Q(user__first_name__icontains=q)
                | Q(user__last_name__icontains=q)
                | Q(user__username__icontains=q)
                | Q(bio__icontains=q)
                | Q(services__icontains=q)
            )
        if data["category"]:
            profiles = profiles.filter(categories=data["category"])
        if data["city"]:
            profiles = profiles.filter(city__icontains=data["city"].strip())
        if data["min_price"] is not None:
            profiles = profiles.filter(price_per_hour__gte=data["min_price"])
        if data["max_price"] is not None:
            profiles = profiles.filter(price_per_hour__lte=data["max_price"])
        sort = data["sort"] or "newest"

    ordering = {
        "newest": "-created_at",
        "price_low": "price_per_hour",
        "price_high": "-price_per_hour",
        "experience": "-experience_years",
    }[sort]
    profiles = profiles.order_by(ordering, "pk").distinct()

    page_obj = Paginator(profiles, 9).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "photographers/list.html", {"form": form, "page_obj": page_obj, "querystring": params.urlencode()})


def photographer_detail(request, pk):
    profile = get_object_or_404(_visible_profiles().prefetch_related("categories", "portfolio"), pk=pk)
    year, month = parse_month(request.GET.get("month"))
    context = {
        "profile": profile,
        "calendar": build_month_calendar(profile, year, month),
        "can_book": request.user.is_authenticated and request.user.role == User.CLIENT,
    }
    return render(request, "photographers/detail.html", context)


# --------------------------------------------------- photographer-only pages
def _my_profile(request):
    return get_object_or_404(PhotographerProfile, user=request.user)


@role_required(User.PHOTOGRAPHER)
def manage_profile(request):
    profile = _my_profile(request)
    user_form = UserBasicsForm(request.POST or None, instance=request.user, prefix="u")
    profile_form = ProfileForm(request.POST or None, request.FILES or None, instance=profile, prefix="p")
    if request.method == "POST" and user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        messages.success(request, "Profile updated.")
        return redirect("photographers:manage_profile")
    return render(request, "photographers/manage_profile.html", {"user_form": user_form, "profile_form": profile_form, "profile": profile})


@role_required(User.PHOTOGRAPHER)
def manage_portfolio(request):
    profile = _my_profile(request)
    if request.method == "POST":
        files = request.FILES.getlist("images")
        caption = request.POST.get("caption", "").strip()[:120]
        existing = profile.portfolio.count()
        if not files:
            messages.error(request, "Please choose at least one image.")
        elif len(files) > MAX_UPLOADS_AT_ONCE:
            messages.error(request, f"Upload at most {MAX_UPLOADS_AT_ONCE} images at a time.")
        elif existing + len(files) > MAX_PORTFOLIO_IMAGES:
            messages.error(request, f"Your portfolio can hold {MAX_PORTFOLIO_IMAGES} images. You have {existing}.")
        else:
            checker = forms.ImageField(validators=[validate_image_size])
            added = 0
            for f in files:
                try:
                    checker.clean(f)  # verifies it is a real image and not too big
                except ValidationError as exc:
                    messages.error(request, f"{f.name}: {exc.messages[0]}")
                    continue
                PortfolioImage.objects.create(profile=profile, image=f, caption=caption)
                added += 1
            if added:
                messages.success(request, f"{added} image(s) added to your portfolio.")
        return redirect("photographers:manage_portfolio")
    return render(request, "photographers/manage_portfolio.html", {"profile": profile, "images": profile.portfolio.all()})


@role_required(User.PHOTOGRAPHER)
@require_POST
def delete_portfolio_image(request, pk):
    image = get_object_or_404(PortfolioImage, pk=pk, profile=_my_profile(request))
    image.image.delete(save=False)  # also removes the file from storage (local disk or S3)
    image.delete()
    messages.success(request, "Image deleted.")
    return redirect("photographers:manage_portfolio")


@role_required(User.PHOTOGRAPHER)
def manage_availability(request):
    profile = _my_profile(request)
    form = BlockedDateForm(request.POST or None, profile=profile)
    if request.method == "POST" and form.is_valid():
        blocked = form.save(commit=False)
        blocked.profile = profile
        blocked.save()
        messages.success(request, "Date marked as unavailable.")
        return redirect("photographers:manage_availability")
    year, month = parse_month(request.GET.get("month"))
    upcoming = profile.blocked_dates.filter(date__gte=timezone.localdate())
    return render(
        request,
        "photographers/manage_availability.html",
        {"profile": profile, "form": form, "calendar": build_month_calendar(profile, year, month), "upcoming": upcoming},
    )


@role_required(User.PHOTOGRAPHER)
@require_POST
def remove_blocked_date(request, pk):
    blocked = get_object_or_404(BlockedDate, pk=pk, profile=_my_profile(request))
    blocked.delete()
    messages.success(request, "Date is available again.")
    return redirect("photographers:manage_availability")
