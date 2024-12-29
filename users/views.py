from rest_framework import generics, status
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
)
from rest_framework.views import APIView
from rest_framework.response import Response
from .utils import api_response


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
            user.save()
            refresh = RefreshToken.for_user(user)
            return api_response(
                True,
                "Verification successful. User logged in.",
                {"refresh": str(refresh), "access": str(refresh.access_token)},
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

                return api_response(
                    True,
                    "Login successful.",
                    {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                        "user": {
                            "id": user.id,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
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
            False, "Login failed.", serializer.errors, status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
    
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
