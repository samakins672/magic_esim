from django.urls import path
from .views import eSIMPlanListView, eSIMProfileView

urlpatterns = [
    path('plans/', eSIMPlanListView.as_view(), name='esim-plans-list'),
    path('profile/', eSIMProfileView.as_view(), name='esim-profile'),
]
