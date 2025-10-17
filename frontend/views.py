from django.contrib.auth import logout
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import json
import os


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
def settings(request):
    context = {
        'user': request.user
    }
    return render(request, 'settings.html', context)


@login_required
def hyperpay_copy_pay(request):
    checkout_id = request.GET.get('checkoutId')

    if not checkout_id:
        return HttpResponseBadRequest("Missing checkoutId")

    context = {
        'checkout_id': checkout_id,
        'reference': request.GET.get('ref'),
        'widget_url': settings.HYPERPAY_PAYMENT_WIDGET_URL,
        'allowed_brands': settings.HYPERPAY_ALLOWED_BRANDS,
        'return_url': settings.HYPERPAY_RETURN_URL,
        'entity_id': settings.HYPERPAY_ENTITY_ID,
    }

    return render(request, 'hyperpay_copy_pay.html', context)
