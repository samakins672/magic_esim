from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    username = models.CharField(max_length=15, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)

    REQUIRED_FIELDS = ['username']
    USERNAME_FIELD = 'email'  # Or 'phone_number' if you want phone-based authentication

    def set_otp(self):
        from random import randint
        from datetime import datetime, timedelta
        self.otp = str(randint(1000, 999999))  # 4-6 digit OTP
        self.otp_expiry = datetime.now() + timedelta(minutes=10)  # OTP valid for 10 minutes
        self.save()
