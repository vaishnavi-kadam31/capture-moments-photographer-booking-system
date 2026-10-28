from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-dashboard/users/<int:pk>/toggle/", views.toggle_user_active, name="toggle_user"),
    path("admin-dashboard/bookings/<int:pk>/cancel/", views.admin_cancel_booking, name="admin_cancel_booking"),
]
