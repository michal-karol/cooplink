from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .views import profile_view, register_view

app_name = "accounts"

urlpatterns = [
    path("register/", register_view, name="register"),
    path(
        "login/",
        # use django built-in login view with login.html emplate
        LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", profile_view, name="profile"),
]