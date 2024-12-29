from rest_framework import serializers
from .models import User
from django.utils.timezone import now
import uuid


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "referral_code",
        ]

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            phone_number=validated_data["phone_number"],
            referral_code=validated_data["referral_code"],
        )
        user.username = f"{user.first_name}_{user.last_name}_{uuid.uuid4()}"
        user.set_password(validated_data["password"])
        user.save()
        return user


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)

    def validate(self, data):
        email = data.get("email")
        phone_number = data.get("phone_number")

        if not email and not phone_number:
            raise serializers.ValidationError(
                "Either email or phone number is required."
            )

        # Check if the user exists
        user = (
            User.objects.filter(email=email)
            if email
            else User.objects.filter(phone_number=phone_number)
        )
        if not user.exists():
            raise serializers.ValidationError("User does not exist.")

        return data


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get("email")
        phone_number = data.get("phone_number")
        otp = data.get("otp")

        user = (
            User.objects.filter(email=email)
            if email
            else User.objects.filter(phone_number=phone_number)
        )
        if not user.exists():
            raise serializers.ValidationError("User does not exist.")

        user = user.first()
        if user.otp != otp:
            raise serializers.ValidationError("Invalid OTP.")
        if user.otp_expiry < now():
            raise serializers.ValidationError("OTP has expired.")

        return user


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "profile_image",
        ]

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")

        # Check if the user exists
        user = User.objects.filter(email=email).first()
        if user is None:
            raise serializers.ValidationError("User with this email does not exist.")

        # Verify the user is active
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")

        # Verify the user is verified
        if not user.is_verified:
            raise serializers.ValidationError(
                "Please verify your email before logging in."
            )

        return data
