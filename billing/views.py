from rest_framework import generics, status
from rest_framework.views import APIView
from magic_esim.permissions import IsAuthenticatedWithSessionOrJWT
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Payment
from esim.utils import fetch_esim_plan_details
from .serializers import PaymentSerializer
from billing.utils import (
    CoinPayments,
    create_copy_and_pay_checkout,
    create_mpgs_checkout,
    get_copy_and_pay_payment_status,
    get_mpgs_payment_status,
    normalize_copy_and_pay_checkout_id,
)
from django.conf import settings
from rest_framework import serializers
from datetime import timedelta
from django.utils.timezone import now
import datetime
from django.urls import reverse
from urllib.parse import urlencode


class PaymentListCreateView(generics.ListCreateAPIView):
    """
    Handles listing all payments and creating a new payment.
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticatedWithSessionOrJWT]

    def get_queryset(self):
        # Only return payments belonging to the authenticated user
        return Payment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Save the payment instance with user details
        payment = serializer.save(user=self.request.user)

        if payment.payment_gateway == 'CoinPayments':
            # Initialize CoinPayments API
            cp = CoinPayments(publicKey=settings.COINPAYMENTS_PUBLIC_KEY, 
                               privateKey=settings.COINPAYMENTS_PRIVATE_KEY,
                               ipn_url=settings.COINPAYMENTS_IPN_URL)

            # Create a CoinPayments transaction
            response = cp.createTransaction({
                'amount': payment.price,
                'currency1': payment.currency,  # User's currency
                'currency2': 'BTC',            # Crypto currency for payment
                'buyer_email': self.request.user.email,
                'item_name': f"Payment for {payment.ref_id}",
                'custom': str(payment.ref_id),  # Reference for later tracking
                'ipn_url': settings.COINPAYMENTS_IPN_URL,
            })
            plan_details = fetch_esim_plan_details(payment.package_code, seller=payment.seller)
            if payment.seller == 'esimgo':
                # Fetch eSIM plan details
                esim_plan = plan_details['description']
            else:
                esim_plan = plan_details['obj']['packageList'][0]['name']

            if response.get('error') == 'ok':
                # Save transaction details if creation is successful
                payment.status = 'PENDING'
                payment.esim_plan = esim_plan
                payment.payment_address = response['address']
                payment.payment_url = response['checkout_url']
                payment.gateway_transaction_id = response['txn_id']
                payment.expiry_datetime = now() + timedelta(seconds=response['timeout'])
                payment.save()
                # Add transaction response to the API response
                self.response_data = {
                    "status": True,
                    "message": "Payment created successfully.",
                    "data": serializer.data,
                    "transaction": response
                }
            else:
                # Handle errors (e.g., raise validation error)
                raise serializers.ValidationError({"status": False, "message": response.get('error')})
        elif payment.payment_gateway == 'HyperPayMPGS':
            plan_details = fetch_esim_plan_details(payment.package_code, seller=payment.seller)
            if payment.seller == 'esimgo':
                # Fetch eSIM plan details
                esim_plan = plan_details['description']
            else:
                esim_plan = plan_details['obj']['packageList'][0]['name']

            mpgs_response = create_mpgs_checkout(
                amount=payment.price,
                currency=payment.currency,
                customer_email=self.request.user.email,
                reference_id=str(payment.ref_id),
                description=f"Payment for {esim_plan} eSIM plan"
            )

            if mpgs_response.get("status"):
                # Save transaction details if creation is successful
                payment.status = 'PENDING'
                payment.esim_plan = esim_plan
                payment.payment_url = mpgs_response["checkout_url"]
                payment.gateway_transaction_id = mpgs_response["payment_id"]
                payment.expiry_datetime = mpgs_response['timeout']
                payment.save()

                self.response_data = {
                    "status": True,
                    "message": "Payment created successfully.",
                    "data": serializer.data,
                }
            else:
                raise serializers.ValidationError({"status": False, "message": mpgs_response.get("message")})
        elif payment.payment_gateway == 'HyperPayCopyAndPay':
            plan_details = fetch_esim_plan_details(payment.package_code, seller=payment.seller)
            if payment.seller == 'esimgo':
                esim_plan = plan_details['description']
            else:
                esim_plan = plan_details['obj']['packageList'][0]['name']

            return_url = settings.HYPERPAY_RETURN_URL or self.request.build_absolute_uri(
                reverse('frontend:hyperpay_copy_pay_result')
            )
            query_string = urlencode({"ref": payment.ref_id})
            separator = "&" if "?" in return_url else "?"
            shopper_result_url = f"{return_url}{separator}{query_string}"

            copy_pay_response = create_copy_and_pay_checkout(
                amount=payment.price,
                currency=payment.currency,
                customer_email=self.request.user.email,
                reference_id=str(payment.ref_id),
                description=f"Payment for {esim_plan} eSIM plan",
                shopper_result_url=shopper_result_url,
            )

            if copy_pay_response.get("status"):
                payment.status = 'PENDING'
                payment.esim_plan = esim_plan
                normalized_checkout_id = normalize_copy_and_pay_checkout_id(
                    copy_pay_response["payment_id"]
                )
                payment.gateway_transaction_id = normalized_checkout_id
                payment.expiry_datetime = copy_pay_response.get('timeout')

                checkout_url = self.request.build_absolute_uri(
                    reverse('frontend:hyperpay_copy_pay')
                )
                payment.payment_url = (
                    f"{checkout_url}?checkoutId={normalized_checkout_id}"
                    f"&ref={payment.ref_id}"
                )
                payment.save()

                self.response_data = {
                    "status": True,
                    "message": "Payment created successfully.",
                    "data": serializer.data,
                }
            else:
                raise serializers.ValidationError(
                    {"status": False, "message": copy_pay_response.get("message")}
                )
        else:
            # Default response if no payment gateway is used
            self.response_data = {
                "status": True,
                "message": "Payment created successfully.",
                "data": serializer.data
            }

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(self.response_data, status=status.HTTP_201_CREATED)


class PaymentStatusCheckView(APIView):
    """
    Check the status of a payment.
    """
    permission_classes = [AllowAny]

    def get(self, request, ref_id):
        try:
            payment = Payment.objects.get(ref_id=ref_id)
        except Payment.DoesNotExist:
            return Response({"status": False, "message": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        if payment.payment_gateway == 'HyperPayMPGS':
            status_response = get_mpgs_payment_status(str(payment.ref_id))
            payment_status = (status_response.get("status") or "").upper()

            if payment_status in ["CAPTURED", "APPROVED", "SUCCESS", "SUCCESSFUL"]:
                payment.status = "COMPLETED"
                payment.date_paid = now()
            elif payment_status in ["PENDING", "IN_PROGRESS", "INITIATED", "AUTHORIZED", "AUTHORISED"]:
                payment.status = "PENDING"
            else:
                payment.status = "FAILED"

            payment.save()

            return Response({
                "status": True,
                "message": "Payment status checked successfully.",
                "data": {
                    "ref_id": payment.ref_id,
                    "status": payment.status,
                    "amount": payment.price,
                    "date_created": payment.date_created,
                    "expiry_datetime": payment.expiry_datetime,
                    "currency": payment.currency,
                    "payment_gateway": payment.payment_gateway,
                    "transaction_id": payment.gateway_transaction_id,
                },
            })

        if payment.payment_gateway == 'HyperPayCopyAndPay':
            checkout_id = normalize_copy_and_pay_checkout_id(payment.gateway_transaction_id)
            status_response = get_copy_and_pay_payment_status(checkout_id)
            payment_status = (status_response.get("status") or "").upper()

            if payment_status == "COMPLETED":
                payment.status = "COMPLETED"
                payment.date_paid = now()
                if status_response.get("transaction_id"):
                    payment.gateway_transaction_id = normalize_copy_and_pay_checkout_id(
                        status_response["transaction_id"]
                    )
            elif payment_status == "PENDING":
                payment.status = "PENDING"
            else:
                payment.status = "FAILED"

            payment.save()

            return Response({
                "status": True,
                "message": "Payment status checked successfully.",
                "data": {
                    "ref_id": payment.ref_id,
                    "status": payment.status,
                    "amount": payment.price,
                    "date_created": payment.date_created,
                    "expiry_datetime": payment.expiry_datetime,
                    "currency": payment.currency,
                    "payment_gateway": payment.payment_gateway,
                    "transaction_id": payment.gateway_transaction_id,
                    "result_code": status_response.get("result_code"),
                    "result_description": status_response.get("result_description"),
                },
            })

        if payment.payment_gateway == 'CoinPayments':
            cp = CoinPayments(
                publicKey=settings.COINPAYMENTS_PUBLIC_KEY,
                privateKey=settings.COINPAYMENTS_PRIVATE_KEY,
                ipn_url=settings.COINPAYMENTS_IPN_URL
            )

            response = cp.getTransactionInfo({'pmtid': payment.gateway_transaction_id})
            if response.get('error') == 'ok':
                payment_status = response['status_text']

                if response['status_text'] == 'Waiting for buyer funds...':
                    payment_status = 'PENDING'
                elif response['status_text'] == 'Cancelled / Timed Out':
                    payment_status = 'FAILED'
                else:
                    payment_status = 'COMPLETED'
                    payment.date_paid = now()

                payment.status = payment_status
                payment.save()

                return Response({
                    "status": True,
                    "message": "Payment status checked successfully.",
                    "data": {
                        "ref_id": payment.ref_id,
                        "status": payment.status,
                        "amount": payment.price,
                        "date_created": payment.date_created,
                        "expiry_datetime": payment.expiry_datetime,
                        "currency": payment.currency,
                        "payment_gateway": payment.payment_gateway,
                        "transaction_id": payment.gateway_transaction_id,
                    },
                })
            else:
                return Response(
                    {"status": False, "message": response.get('error')},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response({"status": False, "message": "Unsupported payment gateway."}, status=status.HTTP_400_BAD_REQUEST)


class UpdatePendingPaymentsView(APIView):
    """
    Checks and updates the status of all pending payments in the last 48 hours.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Get time threshold for last 48 hours
        time_threshold = now() - datetime.timedelta(hours=48)

        # Fetch payments that are still PENDING within the last 48 hours
        pending_payments = Payment.objects.filter(
            status="PENDING",
            date_created__gte=time_threshold
        )

        if not pending_payments.exists():
            return Response({"status": True, "message": "No pending payments found."}, status=status.HTTP_200_OK)

        updated_payments = []

        for payment in pending_payments:
            if payment.payment_gateway == "HyperPayMPGS":
                status_response = get_mpgs_payment_status(str(payment.ref_id))
                payment_status = (status_response.get("status") or "").upper()

                if payment_status in ["CAPTURED", "APPROVED", "SUCCESS", "SUCCESSFUL"]:
                    payment.status = "COMPLETED"
                    payment.date_paid = now()
                elif payment_status in ["PENDING", "IN_PROGRESS", "INITIATED", "AUTHORIZED", "AUTHORISED"]:
                    payment.status = "PENDING"
                else:
                    payment.status = "FAILED"

            elif payment.payment_gateway == "HyperPayCopyAndPay":
                checkout_id = normalize_copy_and_pay_checkout_id(payment.gateway_transaction_id)
                status_response = get_copy_and_pay_payment_status(checkout_id)
                payment_status = (status_response.get("status") or "").upper()

                if payment_status == "COMPLETED":
                    payment.status = "COMPLETED"
                    payment.date_paid = now()
                    if status_response.get("transaction_id"):
                        payment.gateway_transaction_id = normalize_copy_and_pay_checkout_id(
                            status_response["transaction_id"]
                        )
                elif payment_status == "PENDING":
                    payment.status = "PENDING"
                else:
                    payment.status = "FAILED"

            elif payment.payment_gateway == "CoinPayments":
                # Check status from CoinPayments
                cp = CoinPayments(
                    publicKey=settings.COINPAYMENTS_PUBLIC_KEY,
                    privateKey=settings.COINPAYMENTS_PRIVATE_KEY,
                    ipn_url=settings.COINPAYMENTS_IPN_URL
                )
                response = cp.getTransactionInfo({'pmtid': payment.gateway_transaction_id})
                
                if response.get("error") == "ok":
                    payment_status = response["status_text"]

                    if payment_status == "Waiting for buyer funds...":
                        payment.status = "PENDING"
                    elif payment_status in ["Cancelled / Timed Out"]:
                        payment.status = "FAILED"
                    else:
                        payment.status = "COMPLETED"
                        payment.date_paid = now()
                else:
                    payment.status = "FAILED"

            # Save updated payment
            payment.save()
            updated_payments.append({
                "ref_id": payment.ref_id,
                "status": payment.status,
                "amount": payment.price,
                "currency": payment.currency,
                "payment_gateway": payment.payment_gateway,
                "transaction_id": payment.gateway_transaction_id,
                "date_paid": payment.date_paid
            })

        return Response({
            "status": True,
            "message": "Pending payments updated successfully.",
            "updated_payments": updated_payments
        }, status=status.HTTP_200_OK)
