from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import NumberRequests
from .serializers import NumberRequestResponseSerializer, NumberRequestSerializer
from users.utils import api_response

class NumberRequestView(APIView):
    """
    View to create and save number requests in the database.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Virtual Numbers"],
        summary="Submit a virtual number request",
        request=NumberRequestSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=NumberRequestResponseSerializer,
                description="Request stored and notification email sent.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=NumberRequestResponseSerializer,
                description="Validation failed for the submitted request.",
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                response=NumberRequestResponseSerializer,
                description="Request saved but the notification email failed.",
            ),
        },
    )
    def post(self, request):
        serializer = NumberRequestSerializer(data=request.data)
        if serializer.is_valid():
            # Save the request to the database
            number_request = serializer.save()

            # Send email notification
            subject = "New Virtual Number Request"
            from_email = settings.DEFAULT_FROM_EMAIL  # Ensure this is configured in settings.py
            recipient_list = ["info@esimmagic.com"]

            # Render the email content using a Django template
            html_content = render_to_string("emails/number_request.html", {
                "full_name": number_request.full_name,
                "email": number_request.email,
                "nationality": number_request.nationality,
                "purpose": number_request.purpose,
                "service_country": number_request.service_country,
            })

            # Create the email
            email = EmailMessage(
                subject,
                html_content,
                from_email,
                recipient_list,
            )
            email.content_subtype = "html"  # Specify that this email is in HTML format

            # Send the email
            try:
                email.send()
            except Exception as e:
                return Response({"status": False, "message": "Request saved but email failed.", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"status": True, "message": "Request saved and email sent."}, status=status.HTTP_201_CREATED)
        return api_response(
            False,
            "Virtual number request failed.",
            serializer.errors,
            status.HTTP_400_BAD_REQUEST
        )