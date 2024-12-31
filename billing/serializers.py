from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    ref_id = serializers.UUIDField(read_only=True)  # Ensure ref_id is read-only

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'price', 'currency', 'payment_method', 'package_code', 'seller', 'payment_address',
            'payment_gateway', 'status', 'date_paid', 'ref_id', 'gateway_transaction_id', 'date_created', 'expiry_datetime'
        ]
        read_only_fields = ['ref_id', 'payment_address', 'date_paid', 'date_created', 'expiry_datetime', 'status', 'gateway_transaction_id']  # Make these fields read-only
