from rest_framework import serializers
from .models import eSIMPlan
from billing.models import Payment
from .utils import fetch_esim_plan_details, calculate_expiry_date
from django.contrib.auth import get_user_model


class eSIMPlanFilterSerializer(serializers.Serializer):
    locationCode = serializers.CharField(required=False, allow_blank=True)
    type = serializers.CharField(required=False, allow_blank=True)
    slug = serializers.CharField(required=False, allow_blank=True)
    packageCode = serializers.CharField(required=False, allow_blank=True)
    iccid = serializers.CharField(required=False, allow_blank=True)


class eSIMProfileSerializer(serializers.Serializer):
    orderNo = serializers.CharField(required=False, allow_blank=True)
    iccid = serializers.CharField(required=False, allow_blank=True)
    pager = serializers.DictField(child=serializers.IntegerField(), required=False)
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['pager'] = {
            "pageNum": 1,
            "pageSize": 20
        }
        return representation
    

class eSIMPlanSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    package_code = serializers.CharField(write_only=True)
    payment_ref_id = serializers.UUIDField(write_only=True)
    seller = serializers.CharField(write_only=True)

    class Meta:
        model = eSIMPlan
        fields = '__all__'
        read_only_fields = [
            'name', 'slug', 'currency_code', 'speed', 'description', 'price', 'volume',
            'esim_status', 'duration', 'duration_unit', 'support_top_up_type', 'payment',
            'activated_on', 'expires_on', 'smdp_status'
        ]

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        package_code = validated_data.pop('package_code')
        payment_ref_id = validated_data.pop('payment_ref_id')
        seller = validated_data.pop('seller')

        # Fetch user and payment
        user = self.context['request'].user
        User = get_user_model()
        user = User.objects.get(id=user_id)
        payment = Payment.objects.filter(ref_id=payment_ref_id, user=user).first()
        if not payment or payment.status != 'PENDING':
            raise serializers.ValidationError("Invalid or non-pending payment reference.")

        # Fetch eSIM plan details
        plan_details = fetch_esim_plan_details(package_code)
        if not plan_details:
            raise serializers.ValidationError("Failed to fetch plan details from the eSIM API.")

        # Update payment status to 'COMPLETED'
        payment.status = 'COMPLETED'
        payment.save()

        # Calculate expiry date
        expiry_date = calculate_expiry_date(plan_details['duration'])

        # Create and save the eSIM plan
        esim_plan = eSIMPlan.objects.create(
            user=user,
            payment=payment,
            name=plan_details['name'],
            package_code=package_code,
            slug=plan_details['slug'],
            currency_code=plan_details['currency_code'],
            speed=plan_details['speed'],
            description=plan_details['description'],
            price=plan_details['price'],
            volume=plan_details['volume'],
            smdp_status=plan_details['smdp_status'],
            duration=plan_details['duration'],
            duration_unit=plan_details['duration_unit'],
            support_top_up_type=plan_details['support_top_up_type'],
            expires_on=expiry_date,
            seller=seller,
            esim_status='PAID'
        )
        return esim_plan


    def update(self, instance, validated_data):
        # Allow updating only the status
        if 'status' in validated_data:
            instance.status = validated_data['status']
        instance.save()
        return instance