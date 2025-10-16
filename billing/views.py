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
    create_hyperpay_checkout,
    create_mpgs_checkout_session,
    create_tap_payment,
    get_hyperpay_payment_status,
    get_mpgs_payment_status,
    get_tap_payment_status,
)
from django.conf import settings
from django.urls import reverse
from rest_framework import serializers
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from datetime import timedelta
from django.utils.timezone import now
from django.shortcuts import redirect
import datetime


class PaymentListCreateView(generics.ListCreateAPIView):
    """
    Handles listing all payments and creating a new payment.
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticatedWithSessionOrJWT]

    def get_queryset(self):
        # Only return payments belonging to the authenticated user
        return Payment.objects.filter(user=self.request.user)

    def _resolve_esim_plan(self, payment):
        plan_details = fetch_esim_plan_details(payment.package_code, seller=payment.seller)
        try:
            if payment.seller == 'esimgo':
                return plan_details['description']
            return plan_details['obj']['packageList'][0]['name']
        except (KeyError, IndexError, TypeError):
            raise serializers.ValidationError({"status": False, "message": "Unable to determine eSIM plan details."})

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
            print(response)
            
            esim_plan = self._resolve_esim_plan(payment)
            print(esim_plan)
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
        elif payment.payment_gateway == 'TapPayments':
            esim_plan = self._resolve_esim_plan(payment)
            print(payment.price)
            tap_response = create_tap_payment(
                amount=payment.price,
                currency=payment.currency,
                customer_email=self.request.user.email,
                reference_id=str(payment.ref_id),
                description=f"Payment for {esim_plan} eSIM plan"
            )

            print(esim_plan)
            if tap_response.get("status"):
                # Save transaction details if creation is successful
                payment.status = 'PENDING'
                payment.esim_plan = esim_plan
                payment.payment_url = tap_response["checkout_url"]
                payment.gateway_transaction_id = tap_response["payment_id"]
                payment.expiry_datetime = tap_response['timeout']
                payment.save()

                self.response_data = {
                    "status": True,
                    "message": "Payment created successfully.",
                    "data": serializer.data,
                }
            else:
                raise serializers.ValidationError({"status": False, "message": tap_response.get("message")})
        elif payment.payment_gateway == 'MPGS':
            esim_plan = self._resolve_esim_plan(payment)
            mpgs_response = create_mpgs_checkout_session(
                amount=payment.price,
                currency=payment.currency,
                customer_email=self.request.user.email,
                reference_id=str(payment.ref_id),
                description=f"Payment for {esim_plan} eSIM plan",
            )

            if mpgs_response.get("status"):
                payment.status = 'PENDING'
                payment.esim_plan = esim_plan
                payment.payment_url = mpgs_response["checkout_url"]
                payment.gateway_transaction_id = mpgs_response.get("order_id", str(payment.ref_id))
                payment.expiry_datetime = mpgs_response.get("expires_at")
                payment.save()

                self.response_data = {
                    "status": True,
                    "message": "Payment created successfully.",
                    "data": serializer.data,
                }
            else:
                raise serializers.ValidationError({"status": False, "message": mpgs_response.get("message")})
        elif payment.payment_gateway == 'HyperPay':
            esim_plan = self._resolve_esim_plan(payment)
            hyperpay_response = create_hyperpay_checkout(
                amount=payment.price,
                currency=payment.currency,
                customer_email=self.request.user.email,
                reference_id=str(payment.ref_id),
                description=f"Payment for {esim_plan} eSIM plan",
            )

            if hyperpay_response.get("status"):
                payment.status = 'PENDING'
                payment.esim_plan = esim_plan
                payment.payment_url = hyperpay_response["checkout_url"]
                payment.gateway_transaction_id = hyperpay_response.get("checkout_id")
                payment.expiry_datetime = hyperpay_response.get("expires_at")
                payment.save()

                self.response_data = {
                    "status": True,
                    "message": "Payment created successfully.",
                    "data": serializer.data,
                }
            else:
                raise serializers.ValidationError({"status": False, "message": hyperpay_response.get("message")})
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
        if ref_id == "check":
            gateway = request.GET.get("gateway", "TapPayments")

            if gateway == "TapPayments":
                tap_id = request.GET.get("tap_id") or request.GET.get("transaction_id")
                if not tap_id:
                    return Response({"status": False, "message": "Tap ID is required."}, status=status.HTTP_400_BAD_REQUEST)

                payment = Payment.objects.filter(
                    gateway_transaction_id=tap_id, payment_gateway="TapPayments"
                ).first()
                if not payment:
                    return Response({"status": False, "message": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

                status_response = get_tap_payment_status(tap_id)
                payment_status = status_response.get("status", "ERROR")

                if payment_status == "CAPTURED":
                    payment.status = "COMPLETED"
                    payment.date_paid = now()
                elif payment_status in ["INITIATED", "PENDING"]:
                    payment.status = "PENDING"
                else:
                    payment.status = "FAILED"

                payment.save()
                return redirect('/orders/')

            elif gateway == "MPGS":
                order_id = (
                    request.GET.get("order_id")
                    or request.GET.get("transaction_id")
                    or request.GET.get("session_id")
                )
                if not order_id:
                    return Response({"status": False, "message": "Order ID is required."}, status=status.HTTP_400_BAD_REQUEST)

                payment = Payment.objects.filter(
                    gateway_transaction_id=order_id, payment_gateway="MPGS"
                ).first()
                if not payment:
                    return Response({"status": False, "message": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

                status_response = get_mpgs_payment_status(order_id)
                payment_status = status_response.get("status")

                if payment_status == "COMPLETED":
                    payment.status = "COMPLETED"
                    payment.date_paid = now()
                elif payment_status == "PENDING":
                    payment.status = "PENDING"
                elif payment_status == "ERROR":
                    return Response(status_response, status=status.HTTP_400_BAD_REQUEST)
                else:
                    payment.status = "FAILED"

                payment.save()
                return redirect('/orders/')

            elif gateway == "HyperPay":
                checkout_id = (
                    request.GET.get("checkout_id")
                    or request.GET.get("id")
                    or request.GET.get("transaction_id")
                )
                if not checkout_id:
                    return Response({"status": False, "message": "Checkout ID is required."}, status=status.HTTP_400_BAD_REQUEST)

                payment = Payment.objects.filter(
                    gateway_transaction_id=checkout_id, payment_gateway="HyperPay"
                ).first()
                if not payment:
                    return Response({"status": False, "message": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

                status_response = get_hyperpay_payment_status(checkout_id)
                payment_status = status_response.get("status")

                if payment_status == "COMPLETED":
                    payment.status = "COMPLETED"
                    payment.date_paid = now()
                elif payment_status == "PENDING":
                    payment.status = "PENDING"
                elif payment_status == "ERROR":
                    return Response(status_response, status=status.HTTP_400_BAD_REQUEST)
                else:
                    payment.status = "FAILED"

                payment.save()
                return redirect('/orders/')

            return Response({"status": False, "message": "Unsupported gateway."}, status=status.HTTP_400_BAD_REQUEST)

            # return Response({
            #     "status": True,
            #     "message": "Payment status checked successfully.",
            #     "data": {
            #         "ref_id": payment.ref_id,
            #         "status": payment.status,
            #         "amount": payment.price,
            #         "date_created": payment.date_created,
            #         "date_paid": payment.date_paid,
            #         "currency": payment.currency,
            #         "package_code": payment.package_code,
            #         "payment_gateway": payment.payment_gateway,
            #         "transaction_id": payment.gateway_transaction_id,
            #     },
            # })

        else:
            # Handle CoinPayments transactions
            try:
                payment = Payment.objects.get(ref_id=ref_id)
            except Payment.DoesNotExist:
                return Response({"status": False, "message": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

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
            elif payment.payment_gateway == 'TapPayments':
                status_response = get_tap_payment_status(payment.gateway_transaction_id)
                payment_status = status_response.get("status", "ERROR")

                if payment_status == "CAPTURED":
                    payment.status = "COMPLETED"
                    payment.date_paid = now()
                elif payment_status in ["INITIATED", "PENDING"]:
                    payment.status = "PENDING"
                else:
                    payment.status = "FAILED"

                payment.save()

                return Response({
                    "status": payment_status != "ERROR",
                    "message": "Payment status checked successfully." if payment_status != "ERROR" else status_response.get("message", "Unable to determine payment status."),
                    "data": {
                        "ref_id": payment.ref_id,
                        "status": payment.status,
                        "amount": payment.price,
                        "date_created": payment.date_created,
                        "expiry_datetime": payment.expiry_datetime,
                        "currency": payment.currency,
                        "payment_gateway": payment.payment_gateway,
                        "transaction_id": payment.gateway_transaction_id,
                        "raw_status": payment_status,
                    },
                }, status=status.HTTP_200_OK if payment_status != "ERROR" else status.HTTP_400_BAD_REQUEST)
            elif payment.payment_gateway == 'MPGS':
                status_response = get_mpgs_payment_status(
                    payment.gateway_transaction_id or str(payment.ref_id)
                )
                payment_status = status_response.get("status")

                if payment_status == "COMPLETED":
                    payment.status = "COMPLETED"
                    payment.date_paid = now()
                elif payment_status == "PENDING":
                    payment.status = "PENDING"
                elif payment_status == "ERROR":
                    return Response(status_response, status=status.HTTP_400_BAD_REQUEST)
                else:
                    payment.status = "FAILED"

                payment.save()

                return Response({
                    "status": payment_status != "FAILED",
                    "message": "Payment status checked successfully." if payment_status != "FAILED" else "Payment failed.",
                    "data": {
                        "ref_id": payment.ref_id,
                        "status": payment.status,
                        "amount": payment.price,
                        "date_created": payment.date_created,
                        "expiry_datetime": payment.expiry_datetime,
                        "currency": payment.currency,
                        "payment_gateway": payment.payment_gateway,
                        "transaction_id": payment.gateway_transaction_id,
                        "raw_status": status_response.get("raw_status"),
                    },
                })
            elif payment.payment_gateway == 'HyperPay':
                status_response = get_hyperpay_payment_status(payment.gateway_transaction_id)
                payment_status = status_response.get("status")

                if payment_status == "COMPLETED":
                    payment.status = "COMPLETED"
                    payment.date_paid = now()
                elif payment_status == "PENDING":
                    payment.status = "PENDING"
                elif payment_status == "ERROR":
                    return Response(status_response, status=status.HTTP_400_BAD_REQUEST)
                else:
                    payment.status = "FAILED"

                payment.save()

                return Response({
                    "status": payment_status != "FAILED",
                    "message": "Payment status checked successfully." if payment_status != "FAILED" else "Payment failed.",
                    "data": {
                        "ref_id": payment.ref_id,
                        "status": payment.status,
                        "amount": payment.price,
                        "date_created": payment.date_created,
                        "expiry_datetime": payment.expiry_datetime,
                        "currency": payment.currency,
                        "payment_gateway": payment.payment_gateway,
                        "transaction_id": payment.gateway_transaction_id,
                        "raw_status": status_response.get("raw_status"),
                    },
                })

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
            if payment.payment_gateway == "TapPayments":
                # Fetch TapPayments payment status
                status_response = get_tap_payment_status(payment.gateway_transaction_id)
                payment_status = status_response.get("status", "ERROR")

                if payment_status in ["COMPLETED", "CAPTURED"]:
                    payment.status = "COMPLETED"
                    payment.date_paid = now()
                elif payment_status in ["INITIATED", "PENDING", "AUTHORIZED", "AUTHORISED"]:
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
            elif payment.payment_gateway == "MPGS":
                status_response = get_mpgs_payment_status(
                    payment.gateway_transaction_id or str(payment.ref_id)
                )
                payment_status = status_response.get("status")

                if payment_status == "COMPLETED":
                    payment.status = "COMPLETED"
                    payment.date_paid = now()
                elif payment_status == "PENDING":
                    payment.status = "PENDING"
                else:
                    payment.status = "FAILED"
            elif payment.payment_gateway == "HyperPay":
                status_response = get_hyperpay_payment_status(payment.gateway_transaction_id)
                payment_status = status_response.get("status")

                if payment_status == "COMPLETED":
                    payment.status = "COMPLETED"
                    payment.date_paid = now()
                elif payment_status == "PENDING":
                    payment.status = "PENDING"
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
