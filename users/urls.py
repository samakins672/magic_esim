from django.urls import path
from .views import UserRegistrationView, OTPRequestView, OTPVerifyView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('otp/request/', OTPRequestView.as_view(), name='otp-request'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp-verify'),
]
