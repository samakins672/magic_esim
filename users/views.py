from rest_framework import generics, status
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from magic_esim.permissions import IsAuthenticatedWithSessionOrJWT
from rest_framework.permissions import AllowAny
from django.contrib.auth import logout
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate, login
from .models import User
from .serializers import (
    APIResponseSerializer,
    AuthResponseSerializer,
    ChangePasswordSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    LogoutRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserDetailResponseSerializer,
    UserDetailSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
)
from rest_framework.views import APIView
from .utils import api_response
from datetime import datetime
from django.utils.timezone import now
from rest_framework.response import Response
from .serializers import GoogleAuthSerializer


class GoogleAuthView(generics.GenericAPIView):
    serializer_class = GoogleAuthSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Authentication"],
        summary="Sign in with Google",
        request=GoogleAuthSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=AuthResponseSerializer,
                description="Google sign-in succeeded.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=AuthResponseSerializer,
                description="Google token validation failed.",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            data = serializer.save()
            return Response(
                {
                    "status": True,
                    "message": "Google sign-in successful.",
                    "data": data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                "status": False,
                "message": "Google sign-in failed.",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        summary="Register a new user",
        request=UserRegistrationSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=APIResponseSerializer,
                description="User registered successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=APIResponseSerializer,
                description="Validation failed during registration.",
            ),
        },
    ),
)
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

    @extend_schema(
        tags=["Authentication"],
        summary="Request a one-time password",
        request=OTPRequestSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=APIResponseSerializer,
                description="OTP sent successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=APIResponseSerializer,
                description="OTP request validation failed.",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            user = User.objects.filter(email=email).first()
            
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

    @extend_schema(
        tags=["Authentication"],
        summary="Verify one-time password",
        request=OTPVerifySerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=AuthResponseSerializer,
                description="OTP verified successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=AuthResponseSerializer,
                description="OTP verification failed.",
            ),
        },
    )
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
                        "profile_image": user.profile_image.url if user.profile_image else None,
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

    @extend_schema(
        tags=["Authentication"],
        summary="Authenticate with email and password",
        request=UserLoginSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=AuthResponseSerializer,
                description="Login successful.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=AuthResponseSerializer,
                description="Login validation failed.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                response=AuthResponseSerializer,
                description="Invalid credentials or inactive account.",
            ),
        },
    )
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
                            "email": user.email,
                            "profile_image": user.profile_image.url if user.profile_image else None,
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
        tags=["Authentication"],
        summary="Log out and blacklist refresh token",
        request=LogoutRequestSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=APIResponseSerializer,
                description="Logout completed successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=APIResponseSerializer,
                description="Refresh token was missing or invalid.",
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        # Retrieve the refresh token from the request
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return api_response(
                False, "Refresh token is required.", None, status.HTTP_400_BAD_REQUEST
            )

        try:
            # Attempt to blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Log out the user
            logout(request)
            return api_response(
                True, "Successfully logged out.", None, status.HTTP_200_OK
            )
        except TokenError as e:
            # Handle invalid or expired token errors
            return api_response(
                False,
                "Invalid or expired refresh token.",
                str(e),
                status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # Handle any other unexpected errors
            return api_response(
                False,
                "An error occurred during logout.",
                str(e),
                status.HTTP_400_BAD_REQUEST,
            )

    
@extend_schema_view(
    get=extend_schema(
        tags=["User"],
        summary="Retrieve the authenticated user's profile",
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=UserDetailResponseSerializer,
                description="User profile retrieved successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
        },
    ),
    put=extend_schema(
        tags=["User"],
        summary="Update the authenticated user's profile",
        request=UserDetailSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=UserDetailResponseSerializer,
                description="User profile updated successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=UserDetailResponseSerializer,
                description="Profile update validation failed.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
        },
    ),
    patch=extend_schema(
        tags=["User"],
        summary="Partially update the authenticated user's profile",
        request=UserDetailSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=UserDetailResponseSerializer,
                description="User profile updated successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=UserDetailResponseSerializer,
                description="Profile update validation failed.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
        },
    ),
    delete=extend_schema(
        tags=["User"],
        summary="Deactivate the authenticated user's account",
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                response=APIResponseSerializer,
                description="Account deactivated successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
        },
    ),
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
        data = request.data.copy()

        # Exclude fields if they are empty or if email is passed
        excluded_fields = ['email']
        for field in ['first_name', 'last_name', 'profile_image']:
            if field in data and not data[field]:
                excluded_fields.append(field)

        for field in excluded_fields:
            if field in data:
                data.pop(field)

        serializer = self.get_serializer(instance, data=data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            refreshed = self.get_serializer(instance)
            return api_response(
                True,
                "User details updated successfully.",
                refreshed.data,
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

    @extend_schema(
        tags=["Authentication"],
        summary="Request password reset OTP",
        request=PasswordResetRequestSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=APIResponseSerializer,
                description="Password reset OTP sent.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=APIResponseSerializer,
                description="Password reset request failed.",
            ),
        },
    )
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

    @extend_schema(
        tags=["Authentication"],
        summary="Confirm password reset",
        request=PasswordResetConfirmSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=APIResponseSerializer,
                description="Password reset successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=APIResponseSerializer,
                description="Password reset confirmation failed.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=APIResponseSerializer,
                description="User not found for supplied email.",
            ),
        },
    )
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

    @extend_schema(
        tags=["User"],
        summary="Change the authenticated user's password",
        request=ChangePasswordSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=APIResponseSerializer,
                description="Password changed successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=APIResponseSerializer,
                description="Password change failed.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Authentication credentials were not provided.",
            ),
        },
    )
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
