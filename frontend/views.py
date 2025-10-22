from django.contrib.auth import logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.conf import settings
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


