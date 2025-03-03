from django.urls import path
from .views import PaymentListCreateView, PaymentStatusCheckView, UpdatePendingPaymentsView

urlpatterns = [
    path('payments/', PaymentListCreateView.as_view(), name='payment-list-create'),
    path('payments/status/<str:ref_id>/', PaymentStatusCheckView.as_view(), name='payment-status-check'),
    path("payments/update-pending/", UpdatePendingPaymentsView.as_view(), name="update_pending_payments"),
]
