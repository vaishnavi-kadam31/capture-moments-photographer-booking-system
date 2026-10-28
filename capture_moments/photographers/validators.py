from django.core.exceptions import ValidationError

MAX_IMAGE_MB = 5


def validate_image_size(f):
    if f.size > MAX_IMAGE_MB * 1024 * 1024:
        raise ValidationError(f"Image is too large. Maximum size is {MAX_IMAGE_MB} MB.")
