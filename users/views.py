from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User
from .serializers import (
    UserRegistrationSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    UserDetailSerializer,
    UserLoginSerializer,
)
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


class UserMeView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

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
