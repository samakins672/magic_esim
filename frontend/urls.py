from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('reset-password/', views.reset_password, name='reset-password'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('esims/', views.esim_list, name='esim_list'),
    path('esims/purchase/', views.esim_purchase, name='esim_purchase'),
    path('numbers/', views.number_list, name='number_list'),
    path('numbers/purchase/', views.number_purchase, name='number_purchase'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
]
