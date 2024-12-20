from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField
from django.utils.timezone import now, make_aware
from datetime import datetime, timedelta
from random import randint
from .utils import send_otp_email


naive_datetime = datetime.now()
aware_datetime = make_aware(naive_datetime)

class User(AbstractUser):
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    profile_image = CloudinaryField(
        "attachment",
        default="v1734540380/user.png",
        blank=True,
        null=True,
    )

    REQUIRED_FIELDS = ['username']
    USERNAME_FIELD = 'email'

    def set_otp(self):
        self.otp = str(randint(100000, 999999))  # Generate a 6-digit OTP
        self.otp_expiry = now() + timedelta(minutes=10)  # OTP valid for 10 minutes
        self.save()

        # Send the OTP via email
        send_otp_email(self.email, self.otp)
