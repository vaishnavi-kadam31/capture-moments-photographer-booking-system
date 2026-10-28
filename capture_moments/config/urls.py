from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("photographers/", include("photographers.urls")),
    path("bookings/", include("bookings.urls")),
    path("", include("core.urls")),
]

# While developing locally, Django serves uploaded files itself.
# (On AWS they are served from S3 instead.)
if settings.DEBUG and not settings.USE_S3:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
