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
            'user', 'ref_id', 'esim_plan', 'payment_address', 'payment_url', 'date_paid', 'date_created', 'expiry_datetime', 'status',
            'gateway_transaction_id', 'mpgs_success_indicator', 'mpgs_session_version', 'mpgs_order_amount', 'mpgs_order_currency'
        ]  # Make these fields read-only


class PaymentBasicDataSerializer(serializers.Serializer):
    ref_id = serializers.UUIDField()
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    payment_gateway = serializers.CharField()
    transaction_id = serializers.CharField(allow_blank=True, allow_null=True, required=False)


class PaymentStatusDataSerializer(PaymentBasicDataSerializer):
    date_created = serializers.DateTimeField(required=False)
    expiry_datetime = serializers.DateTimeField(allow_null=True, required=False)


class PaymentStatusResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PaymentStatusDataSerializer()


class MastercardCheckoutSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    session_version = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    success_indicator = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    checkout_script_url = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    merchant_name = serializers.CharField(allow_blank=True, required=False)
    merchant_url = serializers.CharField()
    order_amount = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    order_currency = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    orders_url = serializers.CharField()


class PaymentCreateResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = PaymentSerializer()
    transaction = serializers.JSONField(required=False)
    mastercard = MastercardCheckoutSerializer(required=False)


class PaymentStatusListSerializer(PaymentStatusDataSerializer):
    date_paid = serializers.DateTimeField(allow_null=True, required=False)


class PendingPaymentsResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    updated_payments = PaymentStatusListSerializer(many=True)


class MastercardGatewayResponseSerializer(serializers.Serializer):
    status = serializers.CharField(allow_null=True, required=False)
    payment_method = serializers.CharField(allow_null=True, required=False)


class MastercardCallbackDataSerializer(PaymentBasicDataSerializer):
    indicator_matched = serializers.BooleanField(allow_null=True, required=False)


class MastercardCallbackResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = MastercardCallbackDataSerializer()
    gateway_response = MastercardGatewayResponseSerializer(required=False)
