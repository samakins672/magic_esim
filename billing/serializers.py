from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    ref_id = serializers.UUIDField(read_only=True)  # Ensure ref_id is read-only

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'price', 'payment_method',
            'payment_gateway', 'status', 'date_paid', 'ref_id'
        ]
        read_only_fields = ['ref_id', 'date_paid', 'status']  # Make these fields read-only
