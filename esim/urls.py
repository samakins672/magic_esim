from django.urls import path
from .views import (
    eSIMPlanListView,
    ESIMGoPlanDetailView, 
    eSIMProfileView, 
    eSIMPlanListCreateView, 
    eSIMPlanDetailView,
    CountriesListView,
    PopularCountriesListView
)

urlpatterns = [
    path('plans/', eSIMPlanListView.as_view(), name='esim-plans-list'),
    path('plan/esimgo/', ESIMGoPlanDetailView.as_view(), name='esimgo-plan-details'),
    path('profile/', eSIMProfileView.as_view(), name='esim-profile'),
    path('user/plans/', eSIMPlanListCreateView.as_view(), name='user-esim-plan'),
    path('user/plans/<int:pk>/', eSIMPlanDetailView.as_view(), name='user-esim-plan-detail'),
    path('countries/', CountriesListView.as_view(), name='countries-list'),
    path('countries/popular/', PopularCountriesListView.as_view(), name='popular-countries-list'),
]
