from rest_framework import serializers
from .models import User
from django.utils.timezone import now

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'phone_number', 'username']

class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)

    def validate(self, data):
        email = data.get('email')
        phone_number = data.get('phone_number')

        if not email and not phone_number:
            raise serializers.ValidationError("Either email or phone number is required.")

        # Check if the user exists
        user = User.objects.filter(email=email) if email else User.objects.filter(phone_number=phone_number)
        if not user.exists():
            raise serializers.ValidationError("User does not exist.")

        return data

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get('email')
        phone_number = data.get('phone_number')
        otp = data.get('otp')

        user = User.objects.filter(email=email) if email else User.objects.filter(phone_number=phone_number)
        if not user.exists():
            raise serializers.ValidationError("User does not exist.")

        user = user.first()
        if user.otp != otp:
            raise serializers.ValidationError("Invalid OTP.")
        if user.otp_expiry < now():
            raise serializers.ValidationError("OTP has expired.")

        return user
