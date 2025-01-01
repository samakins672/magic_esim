from django.contrib.auth import logout
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

def signup(request):
    return render(request, 'signup.html')

def reset_password(request):
    return render(request, 'reset-password.html')

@login_required
def frontend_logout(request):
    # Log out the user
    logout(request)
    # Redirect to login page
    return redirect('frontend_login')

@login_required
def dashboard(request):
    return render(request, 'dashboard.html', {
        'user': request.user,
        'countries': countries,
        'popular_countries': popular_countries
    })

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
    return render(request, 'esim_list.html', context)

@login_required
def esim_purchase(request):
    context = {
        'user': request.user
    }
    return render(request, 'esim_purchase.html', context)

@login_required
def number_list(request):
    context = {
        'user': request.user
    }
    return render(request, 'number_list.html', context)

@login_required
def number_purchase(request):
    context = {
        'user': request.user
    }
    return render(request, 'number_purchase.html', context)

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
