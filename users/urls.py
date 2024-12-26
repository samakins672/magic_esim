from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView,
    OTPRequestView,
    OTPVerifyView,
    LoginView,
    LogoutView,
    UserMeView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="user-register"),
    path("otp/request/", OTPRequestView.as_view(), name="otp-request"),
    path("otp/verify/", OTPVerifyView.as_view(), name="otp-verify"),
    path("login/", LoginView.as_view(), name="login"),  # Login endpoint
    path('logout/', LogoutView.as_view(), name='logout'),  # Logout endpoint
    path("user/me/", UserMeView.as_view(), name="user-me"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
