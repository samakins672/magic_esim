from django.shortcuts import render
import json
import os

def custom_404(request, exception):
    return render(request, '404.html', status=404)


def index(request):
    json_file_path = os.path.join('static', 'vendor', 'locations', 'countries.json')
    with open(json_file_path, 'r') as file:
        countries = json.load(file)
    return render(request, 'index.html', {'countries': countries})
