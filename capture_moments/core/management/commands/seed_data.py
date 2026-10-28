"""
python manage.py seed_data          -> creates the photography categories (do this once)
python manage.py seed_data --demo   -> also creates demo photographers, a demo client and sample images
"""
import io

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

from accounts.models import User
from photographers.models import Category, PhotographerProfile, PortfolioImage

CATEGORIES = ["Wedding", "Portrait", "Fashion", "Event", "Product", "Travel", "Newborn & Family", "Real Estate"]
DEMO_PASSWORD = "Demo@12345"

DEMO_PHOTOGRAPHERS = [
    ("aarav_lens", "Aarav", "Deshmukh", "Nashik", 8, 2500, ["Wedding", "Event"], ((200, 90, 60), (60, 20, 40))),
    ("meera_frames", "Meera", "Kulkarni", "Pune", 5, 1800, ["Portrait", "Fashion"], ((60, 120, 200), (20, 20, 60))),
    ("rohan_clicks", "Rohan", "Patil", "Mumbai", 12, 4000, ["Wedding", "Travel", "Event"], ((40, 160, 120), (10, 40, 50))),
    ("sana_studio", "Sana", "Sheikh", "Nashik", 3, 1200, ["Newborn & Family", "Portrait", "Product"], ((190, 150, 60), (60, 40, 20))),
]


def make_image(colors, label, size=(900, 600), filename="demo.jpg"):
    """Draw a simple gradient picture so the demo gallery has something to show."""
    top, bottom = colors
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for y in range(size[1]):
        t = y / size[1]
        draw.line([(0, y), (size[0], y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    draw.ellipse([size[0] // 2 - 90, size[1] // 2 - 90, size[0] // 2 + 90, size[1] // 2 + 90], outline=(255, 255, 255), width=6)
    draw.text((30, size[1] - 40), label, fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return ContentFile(buf.getvalue(), name=filename)


class Command(BaseCommand):
    help = "Create categories (and optionally demo data)."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Also create demo users and images")

    def handle(self, *args, **options):
        for name in CATEGORIES:
            Category.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS(f"Categories ready ({len(CATEGORIES)})."))
        if not options["demo"]:
            return

        if not User.objects.filter(username="demo_client").exists():
            User.objects.create_user(
                "demo_client", "demo_client@example.com", DEMO_PASSWORD,
                first_name="Priya", last_name="Sharma", role=User.CLIENT, phone="9876543210",
            )

        for i, (username, first, last, city, years, price, cats, colors) in enumerate(DEMO_PHOTOGRAPHERS):
            if User.objects.filter(username=username).exists():
                continue
            user = User.objects.create_user(
                username, f"{username}@example.com", DEMO_PASSWORD,
                first_name=first, last_name=last, role=User.PHOTOGRAPHER, phone=f"98000000{i:02d}",
            )
            profile = PhotographerProfile.objects.create(
                user=user, city=city, experience_years=years, price_per_hour=price,
                bio=f"Hi, I'm {first}. I love telling stories through photographs and have {years} years of experience.",
                services="\n".join(f"{c} photography" for c in cats) + "\nPhoto editing and retouching\nOnline gallery delivery",
            )
            profile.categories.set(Category.objects.filter(name__in=cats))
            profile.profile_photo.save(f"{username}.jpg", make_image(colors, first, (400, 400), f"{username}.jpg"), save=True)
            for n in range(1, 5):
                shade = tuple(min(255, c + n * 15) for c in colors[0]), colors[1]
                PortfolioImage.objects.create(
                    profile=profile, caption=f"{cats[n % len(cats)]} sample {n}",
                    image=make_image(shade, f"{first} - sample {n}", filename=f"{username}-sample-{n}.jpg"),
                )
        self.stdout.write(self.style.SUCCESS(f"Demo data ready. All demo accounts use password: {DEMO_PASSWORD}"))
        self.stdout.write("Demo client: demo_client | Demo photographers: " + ", ".join(p[0] for p in DEMO_PHOTOGRAPHERS))
