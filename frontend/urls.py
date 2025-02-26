from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'frontend'

urlpatterns = [
    path('new/', views.new_index, name='index'),
    path('new/esim/<str:plan_type>/<str:type>/<str:location_code>/<str:package_code>', views.new_esim, name='esim'),
    path('new/signup/', views.new_signup, name='signup'),
    path('verify/<str:email>', views.verify, name='verify'),
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
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),
    path('sitemap.xml', TemplateView.as_view(template_name="sitemap.xml", content_type='application/xml')),
]
