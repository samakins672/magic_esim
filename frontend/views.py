from django.contrib.auth import logout
from django.conf import settings as django_settings
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.urls import reverse
import json
import os

from billing.models import Payment
from billing.utils import (
    get_copy_and_pay_payment_status,
    normalize_copy_and_pay_checkout_id,
)


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


@login_required
def hyperpay_copy_pay(request):
    checkout_id = normalize_copy_and_pay_checkout_id(request.GET.get('checkoutId'))

    if not checkout_id:
        return HttpResponseBadRequest("Missing checkoutId")

    base_return_url = django_settings.HYPERPAY_RETURN_URL or request.build_absolute_uri(
        reverse('frontend:hyperpay_copy_pay_result')
    )
    customer_ref = request.GET.get('ref')
    if customer_ref:
        separator = '&' if '?' in base_return_url else '?'
        return_url = f"{base_return_url}{separator}ref={customer_ref}"
    else:
        return_url = base_return_url

    context = {
        'checkout_id': checkout_id,
        'reference': customer_ref,
        'widget_url': django_settings.HYPERPAY_PAYMENT_WIDGET_URL,
        'allowed_brands': django_settings.HYPERPAY_ALLOWED_BRANDS,
        'return_url': return_url,
        'entity_id': django_settings.HYPERPAY_ENTITY_ID,
    }

    return render(request, 'hyperpay_copy_pay.html', context)


def hyperpay_copy_pay_result(request):
    checkout_id = normalize_copy_and_pay_checkout_id(
        request.GET.get('id') or request.GET.get('checkoutId')
    )
    resource_path = request.GET.get('resourcePath')

    if not checkout_id and resource_path:
        segments = [segment for segment in resource_path.split('/') if segment]
        if 'checkouts' in segments:
            index = segments.index('checkouts')
            if index + 1 < len(segments):
                checkout_id = normalize_copy_and_pay_checkout_id(segments[index + 1])
        elif segments:
            checkout_id = normalize_copy_and_pay_checkout_id(segments[-1])

    if not checkout_id:
        context = {
            'error': 'Missing HyperPay checkout identifier.',
            'checkout_id': None,
            'status': None,
            'payment': None,
            'result': {},
            'ref': request.GET.get('ref'),
            'raw_payload': '{}',
        }
        return render(request, 'hyperpay_copy_pay_result.html', context, status=400)

    status_response = get_copy_and_pay_payment_status(checkout_id)
    normalized_status = (status_response.get('status') or '').upper()
    transaction_id = normalize_copy_and_pay_checkout_id(
        status_response.get('transaction_id')
    )
    ref_id = request.GET.get('ref')

    payment_qs = Payment.objects.filter(payment_gateway='HyperPayCopyAndPay')
    if ref_id:
        payment_qs = payment_qs.filter(ref_id=ref_id)

    id_candidates = [checkout_id]
    if transaction_id and transaction_id not in id_candidates:
        id_candidates.append(transaction_id)

    payment = payment_qs.filter(gateway_transaction_id__in=id_candidates).first()

    if not payment and ref_id:
        payment = payment_qs.first()

    if payment:
        if normalized_status == 'COMPLETED':
            payment.status = 'COMPLETED'
            payment.date_paid = now()
            if transaction_id:
                payment.gateway_transaction_id = transaction_id
        elif normalized_status == 'PENDING':
            payment.status = 'PENDING'
        elif normalized_status:
            payment.status = 'FAILED'

        payment.save()

    error_message = None
    if normalized_status == 'ERROR':
        error_message = status_response.get('message') or status_response.get('result_description')

    raw_payload = status_response.get('raw') or status_response
    try:
        raw_payload_pretty = json.dumps(raw_payload, indent=2, sort_keys=True)
    except (TypeError, ValueError):
        raw_payload_pretty = str(raw_payload)

    context = {
        'checkout_id': checkout_id,
        'status': normalized_status,
        'payment': payment,
        'result': status_response,
        'ref': ref_id,
        'error': error_message,
        'raw_payload': raw_payload_pretty,
    }

    return render(request, 'hyperpay_copy_pay_result.html', context)
