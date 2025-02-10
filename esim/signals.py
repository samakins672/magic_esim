from django.db.models.signals import post_save
from django.dispatch import receiver
from billing.models import Payment
from .models import eSIMPlan
from .utils import fetch_esim_plan_details, calculate_expiry_date, order_esim_profile
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=Payment)
def handle_payment_completed(sender, instance, **kwargs):
    if instance.status == 'COMPLETED':
        user = instance.user
        package_code = instance.package_code
        payment_ref_id = instance.ref_id
        seller = instance.seller

        # Fetch user and payment
        payment = Payment.objects.filter(ref_id=payment_ref_id, package_code=package_code, user=user).first()
        if not payment or payment.status == 'PENDING':
            raise ValueError("Invalid or pending payment reference.")
        
        if payment.status == 'FAILED':
            raise ValueError("Payment expired.")

        # Fetch eSIM plan details
        plan_details = fetch_esim_plan_details(package_code)
        print(plan_details)
        if not plan_details or plan_details['success'] == False:
            raise ValueError("Failed to fetch plan details from the eSIM API.")

        # Calculate expiry date
        plan_details = plan_details['obj']['packageList'][0]
        expiry_date = calculate_expiry_date(plan_details['duration'])

        plan_price = plan_details['price']
        print(plan_price)
        order_no = order_esim_profile(package_code, payment_ref_id, plan_price)
        print(order_no)

        # Create and save the eSIM plan
        eSIMPlan.objects.create(
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
