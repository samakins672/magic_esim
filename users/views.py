from rest_framework import generics, status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from magic_esim.permissions import IsAuthenticatedWithSessionOrJWT
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import logout
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login
from .models import User
from .serializers import (
    UserRegistrationSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    UserDetailSerializer,
    UserLoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from .utils import api_response
from datetime import datetime
from django.utils.timezone import now


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save(is_verified=False)
        user.set_otp()  # Generate OTP
        # Send OTP via email/SMS (implement sending logic here)
        print(f"OTP sent to {user.email}: {user.otp}")  # Debug only

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return api_response(
                True,
                "Registration successful. Verify OTP to activate your account.",
                None,
                status.HTTP_201_CREATED,
            )
        return api_response(
            False,
            "Registration failed.",
            serializer.errors,
            status.HTTP_400_BAD_REQUEST,
        )


class OTPRequestView(generics.GenericAPIView):
    serializer_class = OTPRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            phone_number = serializer.validated_data.get("phone_number")
            user = (
                User.objects.filter(email=email).first()
                if email
                else User.objects.filter(phone_number=phone_number).first()
            )
            user.set_otp()  # Generate and save OTP
            # Send OTP via email/SMS (implement sending logic here)
            print(f"OTP sent to {user.email}: {user.otp}")  # Debug only
            return api_response(
                True, "OTP sent successfully.", None, status.HTTP_200_OK
            )
        return api_response(
            False, "OTP request failed.", serializer.errors, status.HTTP_400_BAD_REQUEST
        )


class OTPVerifyView(generics.GenericAPIView):
    serializer_class = OTPVerifySerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            user.is_verified = True
            user.otp = None  # Clear OTP
            user.save()
        
            # Log the user in and create a session
            login(request, user)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            # Include access token expiry time
            access_token_expiry = access_token.payload.get("exp")
            
            # Convert Unix timestamp to a datetime object
            expiry_datetime = datetime.fromtimestamp(access_token_expiry)
            
            # Print readable expiry time
            print(f"Access Token Expiry Time: {expiry_datetime}")

            return api_response(
                True,
                "Verification successful. User logged in.",
                {
                    "refresh": str(refresh), 
                    "access": str(access_token),
                    "user": {
                        "id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "phone_number": user.phone_number,
                        "email": user.email
                    }
                },
                status.HTTP_200_OK,
            )
        return api_response(
            False,
            "Verification failed.",
            serializer.errors,
            status.HTTP_400_BAD_REQUEST,
        )


class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            password = serializer.validated_data.get("password")
            user = authenticate(request, email=email, password=password)
            if user is not None:
                # Log the user in and create a session
                login(request, user)

                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token

                # Include access token expiry time
                access_token_expiry = access_token.payload.get("exp")
                
                # Convert Unix timestamp to a datetime object
                expiry_datetime = datetime.fromtimestamp(access_token_expiry)
                
                # Print readable expiry time
                print(f"Access Token Expiry Time: {expiry_datetime}")

                return api_response(
                    True,
                    "Login successful.",
                    {
                        "refresh": str(refresh),
                        "access": str(access_token),
                        "access_token_expiry": access_token_expiry,
                        "user": {
                            "id": user.id,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "phone_number": user.phone_number,
                            "email": user.email,
                            "is_verified": user.is_verified,
                        },
                    },
                    status.HTTP_200_OK,
                )
            return api_response(
                False, "Invalid credentials.", None, status.HTTP_401_UNAUTHORIZED
            )
        return api_response(
            False, serializer.errors, None, status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter("refresh", OpenApiTypes.STR, description="The refresh token to be blacklisted", required=True),
        ],
    )
    def post(self, request, *args, **kwargs):
        try:
            # Blacklist the refresh token
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            # Log out the user
            logout(request)
            return api_response(
                True, "Successfully logged out..", None, status.HTTP_200_OK
            )
        except Exception as e:
            return api_response(
                False, "An error occurred during logout.", str(e), status.HTTP_400_BAD_REQUEST
            )

    
class UserMeView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticatedWithSessionOrJWT]

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return api_response(
            True,
            "User details retrieved successfully.",
            serializer.data,
            status.HTTP_200_OK,
        )

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return api_response(
                True,
                "User details updated successfully.",
                serializer.data,
                status.HTTP_200_OK,
            )
        return api_response(
            False,
            "Update failed.",
            serializer.errors,
            status.HTTP_400_BAD_REQUEST,
        )

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save()
        return api_response(
            True,
            "User account deactivated successfully.",
            None,
            status.HTTP_204_NO_CONTENT,
        )

class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            user.set_otp()  # Generate new OTP
            # TODO: Send OTP via email (implement email sending logic)
            print(f"Password reset OTP for {email}: {user.otp}")  # Debug only
            return api_response(
                True,
                "Password reset OTP has been sent to your email.",
                None,
                status.HTTP_200_OK
            )
        return api_response(
            False,
            "Password reset request failed.",
            serializer.errors,
            status.HTTP_400_BAD_REQUEST
        )

class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            new_password = serializer.validated_data['new_password']
            
            try:
                user = User.objects.get(email=email)
                if user.otp != otp:
                    return api_response(
                        False,
                        "Invalid OTP.",
                        None,
                        status.HTTP_400_BAD_REQUEST
                    )
                if user.otp_expiry < now():
                    return api_response(
                        False,
                        "OTP has expired.",
                        None,
                        status.HTTP_400_BAD_REQUEST
                    )
                
                user.set_password(new_password)
                user.otp = None  # Clear OTP
                user.save()
                
                return api_response(
                    True,
                    "Password has been reset successfully.",
                    None,
                    status.HTTP_200_OK
                )
            except User.DoesNotExist:
                return api_response(
                    False,
                    "User not found.",
                    None,
                    status.HTTP_404_NOT_FOUND
                )
        return api_response(
            False,
            "Password reset failed.",
            serializer.errors,
            status.HTTP_400_BAD_REQUEST
        )

class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticatedWithSessionOrJWT]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return api_response(
                    False,
                    "Current password is incorrect.",
                    None,
                    status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return api_response(
                True,
                "Password changed successfully.",
                None,
                status.HTTP_200_OK
            )
        return api_response(
            False,
            "Password change failed.",
            serializer.errors,
            status.HTTP_400_BAD_REQUEST
        )
