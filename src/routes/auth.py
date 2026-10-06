from django.urls import path

from src.controllers.auth import LoginController


urlpatterns = [
    path(
        "auth/login/",
        LoginController.as_view(),
        name="auth-login",
    ),
]
