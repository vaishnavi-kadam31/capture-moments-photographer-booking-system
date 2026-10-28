from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify

from .validators import validate_image_size


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PhotographerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="photographer_profile")
    categories = models.ManyToManyField(Category, related_name="photographers")
    bio = models.TextField()
    services = models.TextField(help_text="One service per line.")
    experience_years = models.PositiveSmallIntegerField(validators=[MaxValueValidator(60)])
    city = models.CharField(max_length=100)
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(1)])
    profile_photo = models.ImageField(upload_to="profiles/", blank=True, validators=[validate_image_size])
    is_active_listing = models.BooleanField("Visible in search", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def display_name(self):
        return self.user.display_name

    @property
    def services_list(self):
        return [line.strip() for line in self.services.splitlines() if line.strip()]

    def __str__(self):
        return f"{self.display_name} - {self.city}"


class PortfolioImage(models.Model):
    profile = models.ForeignKey(PhotographerProfile, on_delete=models.CASCADE, related_name="portfolio")
    image = models.ImageField(upload_to="portfolio/", validators=[validate_image_size])
    caption = models.CharField(max_length=120, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Portfolio image #{self.pk} of {self.profile.display_name}"


class BlockedDate(models.Model):
    """A day the photographer marks as NOT available (holiday, other work...)."""

    profile = models.ForeignKey(PhotographerProfile, on_delete=models.CASCADE, related_name="blocked_dates")
    date = models.DateField()
    reason = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["date"]
        constraints = [models.UniqueConstraint(fields=["profile", "date"], name="unique_blocked_date_per_photographer")]

    def __str__(self):
        return f"{self.profile.display_name} blocked {self.date}"
