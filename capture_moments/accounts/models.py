from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """One user table for everyone. The `role` field says who they are."""

    CLIENT = "client"
    PHOTOGRAPHER = "photographer"
    ROLE_CHOICES = [(CLIENT, "Client"), (PHOTOGRAPHER, "Photographer")]

    email = models.EmailField("email address", unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=CLIENT)
    phone = models.CharField(
        max_length=16,
        blank=True,
        validators=[RegexValidator(r"^\+?\d{10,15}$", "Enter a valid phone number (10-15 digits, optional +).")],
    )

    @property
    def is_client(self):
        return self.role == self.CLIENT

    @property
    def is_photographer(self):
        return self.role == self.PHOTOGRAPHER

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    def __str__(self):
        return f"{self.display_name} ({self.role})"
