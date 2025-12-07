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
        # ✅ Fetch the user from the Payment instance
        payment = Payment.objects.filter(ref_id=instance.ref_id, package_code=instance.package_code).first()

        if not payment:
            print("⚠ Payment record not found for the given reference ID.")
            return

        # Avoid duplicate eSIM creation for the same payment
        existing_plan = eSIMPlan.objects.filter(payment=payment).first()
        if existing_plan:
            print(f"ℹ eSIM already exists for payment {payment.ref_id} (order_no={existing_plan.order_no}); skipping.")
            return
        
        user = payment.user  # Fetch user from the payment record

        if not user:
            print("⚠ Payment has no associated user!")
            return  # Exit to prevent errors

        package_code = instance.package_code
        payment_ref_id = instance.ref_id
        seller = instance.seller

        if payment.status == 'PENDING':
            print("⚠ Invalid or pending payment reference.")
            return  

        if payment.status == 'FAILED':
            print("⚠ Payment expired.")
            return  

        # Fetch eSIM plan details
        plan_details = fetch_esim_plan_details(package_code, seller)
        print(plan_details)
        if not plan_details or plan_details.get('success') == False:
            print("⚠ Failed to fetch plan details from the eSIM API.")
            return  

        # Calculate expiry date
        plan_details = plan_details['obj']['packageList'][0]
        expiry_date = calculate_expiry_date(plan_details['duration'])

        plan_price = plan_details['price']
        print(plan_price)
        order_no = order_esim_profile(package_code, payment_ref_id, plan_price)
        if not order_no:
            print("⚠ Failed to create eSIM order (orderNo missing). Skipping plan creation.")
            return
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
        print(f"✅ eSIM created for user {user.email} with Order No: {order_no}")
