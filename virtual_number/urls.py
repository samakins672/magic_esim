from django.urls import path
from .views import NumberRequestView

urlpatterns = [
    path('request/', NumberRequestView.as_view(), name='virtual-number-request'),
]