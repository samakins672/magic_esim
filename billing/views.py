from rest_framework import generics, status
from rest_framework.views import APIView
from magic_esim.permissions import IsAuthenticatedWithSessionOrJWT
from rest_framework.response import Response
from .models import Payment
from .serializers import PaymentSerializer
from billing.utils import CoinPayments
from django.conf import settings
from django.urls import reverse
from rest_framework import serializers
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from datetime import timedelta
from django.utils.timezone import now


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
                # 'currency2': 'BTC',            # Crypto currency for payment
                'currency2': 'LTCT',            # Crypto currency for payment
                'buyer_email': self.request.user.email,
                'item_name': f"Payment for {payment.ref_id}",
                'custom': str(payment.ref_id),  # Reference for later tracking
                'ipn_url': settings.COINPAYMENTS_IPN_URL,
            })
            print(response)

            if response.get('error') == 'ok':
                # Save transaction details if creation is successful
                payment.status = 'PENDING'
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
    permission_classes = [IsAuthenticatedWithSessionOrJWT]

    def get(self, request, ref_id):
        # Get the payment instance
        try:
            payment = Payment.objects.get(ref_id=ref_id, user=request.user)
        except Payment.DoesNotExist:
            return Response(
                {"status": False, "message": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if payment.payment_gateway == 'CoinPayments':
            # Initialize CoinPayments API
            cp = CoinPayments(publicKey=settings.COINPAYMENTS_PUBLIC_KEY, 
                               privateKey=settings.COINPAYMENTS_PRIVATE_KEY,
                               ipn_url=settings.COINPAYMENTS_IPN_URL)

            # Check the transaction status
            response = cp.getTransactionInfo({'pmtid': payment.gateway_transaction_id})
            print(response)

            if response.get('error') == 'ok':
                payment_status = response['status_text']  # Human-readable status
                
                if (response['status_text'] == 'Waiting for buyer funds...'):
                    payment_status = 'PENDING'
                else:
                    payment_status = response['COMPLETED']
                    payment.date_paid = now()

                payment.status = payment_status
                payment.save()

                return Response({
                    "status": True,
                    "message": "Payment status fetched successfully.",
                    "data": {
                        "ref_id": payment.ref_id,
                        "status": payment.status,
                        "amount": payment.price,
                        "date_created": payment.date_created,
                        "expiry_datetime": payment.expiry_datetime,
                        "currency": payment.currency,
                        "payment_address": payment.payment_address,
                        "seller": payment.seller,
                        "package_code": payment.package_code,
                        "payment_gateway": payment.payment_gateway,
                        "transaction_id": payment.gateway_transaction_id,
                    },
                })
            else:
                # Handle errors from CoinPayments
                return Response(
                    {"status": False, "message": response.get('error')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"status": False, "message": "Unsupported payment gateway."},
                status=status.HTTP_400_BAD_REQUEST
            )
