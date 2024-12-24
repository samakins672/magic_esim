from django.shortcuts import render
import json
import os

def custom_404(request, exception):
    return render(request, '404.html', status=404)


def index(request):
    # Load all countries
    countries_json_path = os.path.join('static', 'vendor', 'locations', 'countries.json')
    with open(countries_json_path, 'r') as file:
        countries = json.load(file)

    # Load popular countries
    popular_countries_json_path = os.path.join('static', 'vendor', 'locations', 'popular_countries.json')
    with open(popular_countries_json_path, 'r') as file:
        popular_countries = json.load(file)

    # Add `is_popular` key to each country
    popular_country_codes = {country['alpha_2'] for country in popular_countries}
    for country in countries:
        country['is_popular'] = country['alpha_2'] in popular_country_codes

    # Pass both datasets to the template
    return render(request, 'index.html', {
        'countries': countries,
        'popular_countries': popular_countries
    })