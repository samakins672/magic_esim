from google.auth.transport import requests
from google.oauth2 import id_token
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate, login
from django.utils.timezone import now
import uuid


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()

    def validate_id_token(self, value):
        try:
            # Verify the Google token
            google_user = id_token.verify_oauth2_token(value, requests.Request())
            print(google_user)

            if google_user['aud'] not in settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY:
                print(google_user['aud'])
                raise serializers.ValidationError("Invalid Google Client ID.")

            return google_user
        except Exception:
            raise serializers.ValidationError("Invalid Google token.")

    def create(self, validated_data):
        google_user = validated_data["id_token"]
        email = google_user.get("email")
        first_name = google_user.get("given_name", "")
        last_name = google_user.get("family_name", "")
        profile_image = google_user.get("picture", "")

        user, created = User.objects.get_or_create(email=email, defaults={
            "first_name": first_name,
            "last_name": last_name,
            "profile_image": profile_image,
            "is_verified": True,
        })

        request = self.context.get("request")
        if request:
            login(request, user)

        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "profile_image": user.profile_image.url if user.profile_image else None,
                "is_verified": user.is_verified,
            }
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "password",
            "referral_code",
        ]

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            referral_code=validated_data.get("referral_code"),
        )
        user.username = f"{user.first_name}_{str(uuid.uuid4())[:6]}"
        user.set_password(validated_data["password"])
        user.save()
        return user


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)

    def validate(self, data):
        email = data.get("email")

        if not email:
            raise serializers.ValidationError({"error": "Email is required."})

        # Check if the user exists
        user = User.objects.filter(email=email)
        
        if not user.exists():
            raise serializers.ValidationError({"error": "User does not exist."})

        return data


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get("email")
        otp = data.get("otp")

        user = User.objects.filter(email=email)
        
        if not user.exists():
            raise serializers.ValidationError({"error": "User does not exist."})

        user = user.first()
        if user.otp != otp:
            raise serializers.ValidationError({"error": "Invalid OTP."})
        if user.otp_expiry < now():
            raise serializers.ValidationError({"error": "OTP has expired."})

        return user


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "profile_image",
            "is_verified",
        ]

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise serializers.ValidationError({"error": "Email and password are required."})

        # Check if the user exists
        user = User.objects.filter(email=email).first()
        if user is None:
            raise serializers.ValidationError({"error": "User with this email does not exist."})

        # Verify the user is active
        if not user.is_active:
            raise serializers.ValidationError({"error": "This account is inactive."})

        # Verify the user is verified
        if not user.is_verified:
            raise serializers.ValidationError({"error": "Please verify your email before logging in."})

        return data

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"error": "Passwords don't match"})
        return data

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"error": "New passwords don't match"})
        return data


class APIResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.JSONField(required=False, allow_null=True)
    errors = serializers.JSONField(required=False, allow_null=True)


class AuthenticatedUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField(allow_blank=True, allow_null=True)
    last_name = serializers.CharField(allow_blank=True, allow_null=True)
    email = serializers.EmailField()
    profile_image = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    is_verified = serializers.BooleanField()


class TokenPairSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()
    access_token_expiry = serializers.IntegerField(required=False)
    user = AuthenticatedUserSerializer()


class AuthResponseSerializer(APIResponseSerializer):
    data = TokenPairSerializer(required=False)


class UserDetailResponseSerializer(APIResponseSerializer):
    data = UserDetailSerializer(required=False)


class LogoutRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()
