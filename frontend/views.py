from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def index(request):
    return render(request, 'index.html')

def signup(request):
    return render(request, 'signup.html')

def login(request):
    return render(request, 'login.html')

def reset_password(request):
    return render(request, 'reset-password.html')

@login_required
def dashboard(request):
    context = {
        'user': request.user
    }
    return render(request, 'dashboard.html', context)

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
