from django.urls import path
from .views import (
    UserRegistrationView,
    OTPRequestView,
    OTPVerifyView,
    LoginView,
    UserMeView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="user-register"),
    path("otp/request/", OTPRequestView.as_view(), name="otp-request"),
    path("otp/verify/", OTPVerifyView.as_view(), name="otp-verify"),
    path("login/", LoginView.as_view(), name="login"),  # Login endpoint
    path("user/me/", UserMeView.as_view(), name="user-me"),
]
