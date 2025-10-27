from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse

def api_response(status: bool, message: str, data=None, http_status=200):
    """
    Custom response handler to format API responses.
    :param status: Boolean indicating success or failure.
    :param message: A string message to describe the response.
    :param data: The data payload (default: None).
    :param http_status: HTTP status code (default: 200).
    :return: Response object.
    """
    from rest_framework.response import Response

    return Response(
        {"status": status, "message": message, "data": data}, status=http_status
    )


def send_otp_email(user_email, otp):
    """
    Sends an OTP to the user's email in HTML format.
    :param user_email: The recipient's email address.
    :param otp: The OTP to send.
    """
    subject = "Your OTP Code"
    from_email = settings.DEFAULT_FROM_EMAIL  # Ensure this is configured in settings.py
    recipient_list = [user_email]

    # Render the email content using a Django template
    html_content = render_to_string("emails/otp_email.html", {"otp": otp})

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
        print(f"OTP email sent to {user_email}")  # For debugging
    except Exception as e:
        print(f"Error sending email to {user_email}: {e}")


def send_account_deletion_email(user_email: str, delete_url: str):
    """
    Sends an account deletion confirmation email with a unique link.

    :param user_email: Recipient email address.
    :param delete_url: Absolute URL to confirm deletion.
    """
    subject = "Confirm your account deletion"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user_email]

    html_content = render_to_string(
        "emails/account_deletion_email.html",
        {"delete_url": delete_url},
    )

    email = EmailMessage(
        subject,
        html_content,
        from_email,
        recipient_list,
    )
    email.content_subtype = "html"

    try:
        email.send()
        print(f"Account deletion email sent to {user_email}")
    except Exception as e:
        print(f"Error sending account deletion email to {user_email}: {e}")
