from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField

class User(AbstractUser):
    username = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    profile_image = CloudinaryField( "attachment", default="v1720162905/user.png", blank=True, null=True, )

    REQUIRED_FIELDS = ['username']
    USERNAME_FIELD = 'email'

    def set_otp(self):
        from random import randint
        from datetime import datetime, timedelta
        self.otp = str(randint(1000, 999999))  # 4-6 digit OTP
        self.otp_expiry = datetime.now() + timedelta(minutes=10)  # OTP valid for 10 minutes
        self.save()
