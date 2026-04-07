from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
	path("register/", views.RegisterView.as_view(), name="register"),
	path("login/", views.CustomLoginView.as_view(), name="login"),
	path("password/help/", views.PasswordHelpView.as_view(), name="password_help"),
	path("logout/", views.CustomLogoutView.as_view(), name="logout"),
	path("profile/<int:pk>/", views.UserProfileView.as_view(), name="profile"),
	path("profile/<int:pk>/edit/", views.UserProfileEditView.as_view(), name="profile_edit"),
	path("password/change/", views.PasswordChangeCustomView.as_view(), name="password_change"),
	path("users/", views.UserListView.as_view(), name="user_list"),
]
