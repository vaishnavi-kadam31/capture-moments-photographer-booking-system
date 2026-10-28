from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/client/", views.register_client, name="register_client"),
    path("register/photographer/", views.register_photographer, name="register_photographer"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
