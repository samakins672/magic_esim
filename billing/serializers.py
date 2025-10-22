from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    ref_id = serializers.UUIDField(read_only=True)  # Ensure ref_id is read-only

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'price', 'currency', 'payment_method', 'package_code', 'esim_plan', 'seller', 'payment_address', 'payment_url',
            'payment_gateway', 'status', 'date_paid', 'ref_id', 'gateway_transaction_id', 'date_created', 'expiry_datetime',
            'mpgs_success_indicator', 'mpgs_session_version', 'mpgs_order_amount', 'mpgs_order_currency'
        ]
        read_only_fields = [
            'ref_id', 'esim_plan', 'payment_address', 'payment_url', 'date_paid', 'date_created', 'expiry_datetime', 'status',
            'gateway_transaction_id', 'mpgs_success_indicator', 'mpgs_session_version', 'mpgs_order_amount', 'mpgs_order_currency'
        ]  # Make these fields read-only
