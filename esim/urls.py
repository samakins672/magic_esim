from django.urls import path
from .views import (
    eSIMPlanListView, 
    eSIMProfileView, 
    eSIMPlanListCreateView, 
    eSIMPlanDetailView,
    CountriesListView
)

urlpatterns = [
    path('plans/', eSIMPlanListView.as_view(), name='esim-plans-list'),
    path('profile/', eSIMProfileView.as_view(), name='esim-profile'),
    path('user/plans/', eSIMPlanListCreateView.as_view(), name='user-esim-plan'),
    path('user/plans/<int:pk>/', eSIMPlanDetailView.as_view(), name='user-esim-plan-detail'),
    path('countries/', CountriesListView.as_view(), name='countries-list'),
]
