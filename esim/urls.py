from django.urls import path
from .views import eSIMPlanListView

urlpatterns = [
    path('plans/', eSIMPlanListView.as_view(), name='esim-plans-list'),
]
