from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("book/<int:photographer_id>/", views.create_booking, name="create"),
    path("my/", views.client_dashboard, name="client_dashboard"),
    path("my/<int:pk>/cancel/", views.cancel_booking, name="cancel"),
    path("requests/", views.photographer_dashboard, name="photographer_dashboard"),
    path("requests/<int:pk>/<str:action>/", views.respond_booking, name="respond"),
    path("notifications/", views.notifications_list, name="notifications"),
]
