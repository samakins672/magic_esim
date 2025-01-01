from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('reset-password/', views.reset_password, name='reset-password'),
    path('logout/', views.frontend_logout, name='frontend_logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('esims/', views.esim_list, name='esim_list'),
    path('orders/', views.orders, name='esim_orders'),
    path('numbers/', views.number_list, name='number_list'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
]
