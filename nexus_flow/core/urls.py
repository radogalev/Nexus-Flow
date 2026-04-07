from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("landing/", views.LandingView.as_view(), name="landing"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("privacy/", views.PrivacyView.as_view(), name="privacy"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("notifications/", views.NotificationListView.as_view(), name="notifications"),
    path("notifications/mark-all-read/", views.NotificationMarkAllReadView.as_view(), name="notifications_mark_all_read"),
    path("notifications/<int:pk>/open/", views.NotificationOpenView.as_view(), name="notification_open"),
]
