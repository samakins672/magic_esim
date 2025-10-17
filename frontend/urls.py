from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.index, name='index'),
    path('esim/<str:plan_type>/<str:type>/<str:location_code>/<str:package_code>', views.esim, name='esim'),
    path('verify/<str:email>', views.verify, name='verify'),
    path('signup/', views.signup, name='signup'),
    path('reset-password/', views.reset_password, name='reset-password'),
    path('logout/', views.frontend_logout, name='frontend_logout'),
    path('esims/', views.esim_list, name='esim_list'),
    path('orders/', views.orders, name='esim_orders'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.account_settings, name='settings'),
    path('payments/hyperpay/copy-pay/', views.hyperpay_copy_pay, name='hyperpay_copy_pay'),
    path('payments/hyperpay/result/', views.hyperpay_copy_pay_result, name='hyperpay_copy_pay_result'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),
    path('sitemap.xml', TemplateView.as_view(template_name="sitemap.xml", content_type='application/xml')),
]
