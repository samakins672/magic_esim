from rest_framework import serializers
from .models import eSIMPlan
from billing.models import Payment
from .utils import fetch_esim_plan_details, calculate_expiry_date, order_esim_profile


class eSIMPlanFilterSerializer(serializers.Serializer):
    locationCode = serializers.CharField(required=False, allow_blank=True)
    type = serializers.CharField(required=False, allow_blank=True)
    slug = serializers.CharField(required=False, allow_blank=True)
    packageCode = serializers.CharField(required=False, allow_blank=True)
    iccid = serializers.CharField(required=False, allow_blank=True)
    mainRegion = serializers.CharField(required=False, allow_blank=True)


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
    package_code = serializers.CharField(write_only=True)
    payment_ref_id = serializers.UUIDField(write_only=True)
    seller = serializers.CharField(write_only=True)
    location_code_lower = serializers.SerializerMethodField()

    class Meta:
        model = eSIMPlan
        fields = '__all__'
        read_only_fields = [
            'name', 'slug', 'order_no', 'currency_code', 'speed', 'description', 'price', 'volume',            
            'esim_status', 'duration', 'duration_unit', 'support_top_up_type', 'payment', 'location_code_lower', 
            'activated_on', 'expires_on', 'smdp_status'
        ]

    def get_location_code_lower(self, obj):
        # Return the lowercase version of location_code
        return obj.location_code.lower() if obj.location_code else None

    def create(self, validated_data):
        user = validated_data.pop('user')
        package_code = validated_data.pop('package_code')
        payment_ref_id = validated_data.pop('payment_ref_id')
        seller = validated_data.pop('seller')

        # Fetch user and payment
        payment = Payment.objects.filter(ref_id=payment_ref_id, package_code=package_code, user=user).first()
        if not payment or payment.status == 'PENDING':
            raise serializers.ValidationError({'status': False, 'message': "Invalid or pending payment reference."})
        
        if payment.status == 'FAILED':
            raise serializers.ValidationError({'status': False, 'message': "Payment expired."})

        # Fetch eSIM plan details
        plan_details = fetch_esim_plan_details(package_code)
        print(plan_details)
        if not plan_details or plan_details['success'] == False:
            raise serializers.ValidationError({'status': False, 'message': "Failed to fetch plan details from the eSIM API."})

        # Calculate expiry date
        plan_details = plan_details['obj']['packageList'][0]
        expiry_date = calculate_expiry_date(plan_details['duration'])

        plan_price = plan_details['price']
        print(plan_price)
        order_no = order_esim_profile(package_code, payment_ref_id, plan_price)
        print(order_no)

        # Create and save the eSIM plan
        esim_plan = eSIMPlan.objects.create(
            user=user,
            payment=payment,
            order_no=order_no,
            location_code=plan_details['locationNetworkList'][0]['locationCode'],
            name=plan_details['name'],
            package_code=package_code,
            slug=plan_details['slug'],
            currency_code=plan_details['currencyCode'],
            speed=plan_details['speed'],
            description=plan_details['description'],
            price=plan_details['price'],
            volume=plan_details['volume'],
            duration=plan_details['duration'],
            duration_unit=plan_details['durationUnit'],
            support_top_up_type=plan_details['supportTopUpType'],
            expires_on=expiry_date,
            seller=seller,
            esim_status='PAID'
        )
        return esim_plan


class eSIMBaseResponseSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.JSONField(required=False, allow_null=True)
    errors = serializers.JSONField(required=False, allow_null=True)
    error = serializers.JSONField(required=False, allow_null=True)


class eSIMPlanCollectionSerializer(serializers.Serializer):
    standard = serializers.ListField(
        child=serializers.JSONField(),
        help_text="Plans returned from the eSIMAccess catalogue.",
    )
    unlimited = serializers.ListField(
        child=serializers.JSONField(),
        help_text="Plans returned from the eSIMGo catalogue.",
    )


class eSIMPlanListResponseSerializer(eSIMBaseResponseSerializer):
    data = eSIMPlanCollectionSerializer(required=False)


class ESIMGoPlanDetailResponseSerializer(eSIMBaseResponseSerializer):
    data = serializers.JSONField(required=False, allow_null=True)


class eSIMProfileResponseSerializer(eSIMBaseResponseSerializer):
    data = serializers.ListField(
        child=serializers.JSONField(),
        required=False,
        allow_null=True,
    )


class eSIMUserPlanSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order_no = serializers.CharField(allow_blank=True, allow_null=True)
    name = serializers.CharField(allow_blank=True, allow_null=True)
    slug = serializers.CharField(allow_blank=True, allow_null=True)
    package_code = serializers.CharField()
    activated_on = serializers.DateTimeField(allow_null=True)
    volume_used = serializers.CharField(allow_blank=True, allow_null=True)
    esim_status = serializers.CharField()
    duration = serializers.IntegerField()
    currency_code = serializers.CharField()
    speed = serializers.CharField(allow_blank=True, allow_null=True)
    volume = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField()
    seller = serializers.CharField()
    location_code = serializers.CharField(allow_blank=True, allow_null=True)
    location_code_lower = serializers.CharField()
    expires_on = serializers.DateTimeField()
    smdp_status = serializers.CharField()
    duration_unit = serializers.CharField()
    support_top_up_type = serializers.IntegerField()
    usageScale = serializers.FloatField(required=False, allow_null=True)
    durationLeft = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    formattedVolumeLeft = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class eSIMUserPlanListResponseSerializer(eSIMBaseResponseSerializer):
    data = eSIMUserPlanSerializer(many=True, required=False)


class eSIMUserPlanResponseSerializer(eSIMBaseResponseSerializer):
    data = eSIMPlanSerializer(required=False)


class CountrySerializer(serializers.Serializer):
    alpha_2 = serializers.CharField()
    name = serializers.CharField()
    slug = serializers.CharField()
    alpha_2_lower = serializers.CharField()


class CountryListResponseSerializer(eSIMBaseResponseSerializer):
    data = CountrySerializer(many=True, required=False)

