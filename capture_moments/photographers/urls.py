from django.urls import path

from . import views

app_name = "photographers"

urlpatterns = [
    path("", views.photographer_list, name="list"),
    path("<int:pk>/", views.photographer_detail, name="detail"),
    path("manage/profile/", views.manage_profile, name="manage_profile"),
    path("manage/portfolio/", views.manage_portfolio, name="manage_portfolio"),
    path("manage/portfolio/<int:pk>/delete/", views.delete_portfolio_image, name="delete_portfolio_image"),
    path("manage/availability/", views.manage_availability, name="manage_availability"),
    path("manage/availability/<int:pk>/remove/", views.remove_blocked_date, name="remove_blocked_date"),
]
