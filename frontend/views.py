from django.contrib.auth import logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.conf import settings
from django.core import signing
import json
import os

from billing.models import Payment

# Load all countries
countries_json_path = os.path.join('static', 'vendor', 'locations', 'countries.json')
with open(countries_json_path, 'r') as file:
    countries = json.load(file)

# Load popular countries
popular_countries_json_path = os.path.join('static', 'vendor', 'locations', 'popular_countries.json')
with open(popular_countries_json_path, 'r') as file:
    popular_countries = json.load(file)

# Add `is_popular` key to each country
popular_country_codes = {country.get('alpha_2') for country in popular_countries if 'alpha_2' in country}
for country in countries:
    country['is_popular'] = country.get('alpha_2') in popular_country_codes if 'alpha_2' in country else False

def index(request):
    # Pass both datasets to the template
    return render(request, 'index.html', {
        'countries': countries,
        'popular_countries': popular_countries
    })

def esim(request, plan_type, location_code, type, package_code):
    # Find country name based on location_code for single type
    country_name = "Unknown Country"
    
    if type == "single":
        for country in countries:
            if country.get('alpha_2', '').upper() == location_code.upper():
                country_name = country.get('name', 'Unknown Country')
                break
    elif type == "region":
        # You can map location codes for regions if needed
        region_mapping = {
            "GL-12": "Global",
            "GL-13": "Global",
            "GL-14": "Global",
            "AS": "Asia",
            "AF": "Africa",
            "EU": "European Union",
            "CA": "Caribbean",
            "NA": "North America",
            "SA": "South America",
        }
        country_name = region_mapping.get(location_code.upper(), "Unknown Region")

    # Pass data to the template
    return render(request, 'checkout.html', {
        'location_code': location_code,
        'country_name': country_name,
        'plan_type': plan_type,
        'type': type,
        'package_code': package_code
    })

def signup(request):
    return render(request, 'signup.html')

def verify(request, email):
    return render(request, 'verification.html', {
        'email': email
    })

def reset_password(request):
    return render(request, 'reset-password.html')

def reset_password_confirm(request, email, otp):
    return render(request, 'reset-password-confirm.html', {
        'email': email,
        'otp': otp
    })

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_and_conditions(request):
    return render(request, 'terms_and_conditions.html')

@login_required
def frontend_logout(request):
    # Log out the user
    logout(request)
    # Redirect to login page
    return redirect('frontend_login')

@login_required
def orders(request):
    return render(request, 'orders.html', {
        'user': request.user
    })


@login_required
def mastercard_checkout(request, ref_id):
    payment = get_object_or_404(Payment, ref_id=ref_id)

    if payment.user_id != request.user.id:
        return HttpResponseForbidden("You do not have permission to access this payment.")

    if payment.payment_gateway not in ("MastercardHostedCheckout", "HyperPayMPGS"):
        return render(
            request,
            "mastercard_checkout.html",
            {
                "can_launch": False,
                "error_message": "This payment is not configured for Mastercard Hosted Checkout.",
                "orders_url": reverse('frontend:esim_orders'),
            },
            status=400,
        )

    session_id = payment.gateway_transaction_id
    session_version = payment.mpgs_session_version

    if not session_id:
        return render(
            request,
            "mastercard_checkout.html",
            {
                "can_launch": False,
                "error_message": "The hosted checkout session has expired. Please start the payment again.",
                "orders_url": reverse('frontend:esim_orders'),
            },
            status=410,
        )

    checkout_script_url = getattr(settings, "MPGS_CHECKOUT_SCRIPT_URL", None)
    merchant_name = getattr(settings, "MPGS_MERCHANT_NAME", "")
    merchant_url = getattr(settings, "MPGS_MERCHANT_URL", "") or request.build_absolute_uri('/')

    context = {
        "can_launch": True,
        "session_id": str(session_id),
        "session_version": session_version,
        "success_indicator": payment.mpgs_success_indicator,
        "checkout_script_url": checkout_script_url,
        "orders_url": reverse('frontend:esim_orders'),
        "mpgs_merchant_name": merchant_name,
        "mpgs_merchant_url": merchant_url,
        "order_amount": (
            f"{payment.mpgs_order_amount:.2f}" if payment.mpgs_order_amount is not None else ""
        ),
        "order_currency": payment.mpgs_order_currency or "",
        "order_description": payment.esim_plan or "",
    }

    return render(request, "mastercard_checkout.html", context)

@login_required
def esim_list(request):
    context = {
        'user': request.user
    }
    return render(request, 'esims.html', context)

@login_required
def profile(request):
    context = {
        'user': request.user
    }
    return render(request, 'profile.html', context)

@login_required
def account_settings(request):
    context = {
        'user': request.user
    }
    return render(request, 'settings.html', context)



def request_account_deletion(request):
    """Render a form to request account deletion by email, and send confirmation link."""
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()

        # Build deletion link regardless of whether user exists to avoid enumeration
        try:
            from users.models import User
            user = User.objects.filter(email__iexact=email).first()
        except Exception:
            user = None

        if user and user.email:
            # Create signed token with user id
            token = signing.dumps({'uid': user.id}, salt='account-deletion')
            confirm_path = reverse('frontend:confirm_account_deletion', args=[token])
            delete_url = request.build_absolute_uri(confirm_path)

            # Send email
            from users.utils import send_account_deletion_email
            send_account_deletion_email(user.email, delete_url)

        # Always show the same response
        return render(request, 'request_account_deletion_done.html', {
            'submitted_email': email,
        })

    return render(request, 'request_account_deletion.html')


def confirm_account_deletion(request, token: str):
    """Verify token and delete the associated account if valid."""
    context = {}
    try:
        data = signing.loads(token, salt='account-deletion', max_age=60 * 60 * 48)  # 48 hours
        user_id = data.get('uid')
    except signing.BadSignature:
        context['error'] = 'Invalid or tampered link.'
        return render(request, 'account_deleted.html', context, status=400)
    except signing.SignatureExpired:
        context['error'] = 'This link has expired.'
        return render(request, 'account_deleted.html', context, status=410)

    # Delete user if exists
    from users.models import User, AccountDeletionLog
    user = User.objects.filter(id=user_id).first()
    if not user:
        context['message'] = 'Account already deleted.'
        return render(request, 'account_deleted.html', context)

    # Log deletion event for audit
    try:
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = (xff.split(',')[0].strip() if xff else None) or request.META.get('REMOTE_ADDR')
        ua = request.META.get('HTTP_USER_AGENT')
        AccountDeletionLog.objects.create(
            user_pk=user.id,
            email=user.email,
            ip_address=ip,
            user_agent=ua,
            method='self-service',
            request_path=request.path,
        )
    except Exception:
        # Do not block deletion due to logging failure
        pass

    # Perform delete (cascades payments and related objects)
    user.delete()
    context['message'] = 'Your account has been deleted.'
    return render(request, 'account_deleted.html', context)
