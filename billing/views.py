from rest_framework import generics, serializers, status
from rest_framework.views import APIView
from magic_esim.permissions import IsAuthenticatedWithSessionOrJWT
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from .models import Payment
from esim.utils import fetch_esim_plan_details
from .serializers import (
    MastercardCallbackResponseSerializer,
    PaymentCreateResponseSerializer,
    PaymentSerializer,
    PaymentStatusResponseSerializer,
    PendingPaymentsResponseSerializer,
)
from billing.utils import (
    CoinPayments,
    get_mastercard_payment_status,
    initiate_mastercard_checkout,
)
from django.conf import settings
from datetime import timedelta
from django.utils.timezone import now
from django.urls import reverse
import datetime


MPGS_SUCCESS_STATUSES = {"CAPTURED", "APPROVED", "SUCCESS", "SUCCESSFUL", "PAID", "SETTLED"}
MPGS_PENDING_STATUSES = {"PENDING", "IN_PROGRESS", "INITIATED", "AUTHORIZED", "AUTHORISED", "AUTHORISED_PENDING_SETTLEMENT"}


def _apply_mastercard_status(payment, status_response):
    """Normalize Mastercard status payloads to local Payment.

    Default to PENDING unless the API clearly indicates success or a terminal failure
    (expired, failed, cancelled, declined). This prevents prematurely marking
    payments as failed when MPGS is still processing.
    """

    payment_status_raw = status_response.get("status") or ""
    payment_status = str(payment_status_raw).upper()
    updated_fields = []

    # Determine failure by explicit keywords per Retrieve Order semantics.
    # Default to PENDING unless the gateway clearly states expired/failed/cancelled/declined.
    failed_keywords = ("EXPIRE", "FAIL", "CANCEL", "DECLIN")
    is_failed = any(k in payment_status for k in failed_keywords)
    is_success = payment_status in MPGS_SUCCESS_STATUSES
    is_pending = payment_status in MPGS_PENDING_STATUSES

    if is_success:
        if payment.status != "COMPLETED":
            payment.status = "COMPLETED"
            updated_fields.append("status")
        payment.date_paid = now()
        updated_fields.append("date_paid")
    elif is_failed:
        if payment.status != "FAILED":
            payment.status = "FAILED"
            updated_fields.append("status")
    else:
        # Pending by default for unknown/processing states; don't downgrade completed
        if payment.status != "COMPLETED" and payment.status != "PENDING":
            payment.status = "PENDING"
            updated_fields.append("status")

    payment_method = status_response.get("payment_method")
    if payment_method:
        payment.payment_method = payment_method
        updated_fields.append("payment_method")

    raw_payload = status_response.get("raw")
    transaction = None
    if isinstance(raw_payload, dict):
        transactions = raw_payload.get("transactions")
        if isinstance(transactions, list) and transactions:
            transaction = transactions[-1]
        elif isinstance(raw_payload.get("transaction"), dict):
            transaction = raw_payload.get("transaction")

    if isinstance(transaction, dict):
        transaction_id = transaction.get("id") or transaction.get("transactionId")
        if transaction_id:
            payment.gateway_transaction_id = transaction_id
            if "gateway_transaction_id" not in updated_fields:
                updated_fields.append("gateway_transaction_id")

    if updated_fields:
        payment.save(update_fields=updated_fields)
    return payment


@extend_schema_view(
    get=extend_schema(
        tags=["Payments"],
        summary="List authenticated user payments",
        description=(
            "Return every payment created by the authenticated user. "
            "Results are ordered by the default queryset configuration."
        ),
        responses=PaymentSerializer(many=True),
    ),
    post=extend_schema(
        tags=["Payments"],
        summary="Create a payment",
        description=(
            "Create a new payment and initiate the configured payment gateway. "
            "The response wraps the stored payment along with gateway specific metadata."
        ),
        request=PaymentSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=PaymentCreateResponseSerializer,
                description="Payment created successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Validation failed when creating the payment.",
            ),
        },
    ),
)
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
        serializer.instance = payment

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
        elif payment.payment_gateway in ('HyperPayMPGS', 'MastercardHostedCheckout'):
            payment.payment_gateway = 'MastercardHostedCheckout'
            plan_details = fetch_esim_plan_details(payment.package_code, seller=payment.seller)
            if payment.seller == 'esimgo':
                # Fetch eSIM plan details
                esim_plan = plan_details['description']
            else:
                esim_plan = plan_details['obj']['packageList'][0]['name']

            mpgs_response = initiate_mastercard_checkout(
                amount=payment.price,
                currency=payment.currency,
                customer_email=self.request.user.email,
                reference_id=str(payment.ref_id),
                description=esim_plan,
            )

            if mpgs_response.get("status"):
                # Save transaction details if creation is successful
                payment.status = 'PENDING'
                payment.esim_plan = mpgs_response.get("order_description") or esim_plan
                payment.gateway_transaction_id = mpgs_response["payment_id"]
                payment.mpgs_success_indicator = mpgs_response.get("success_indicator")
                payment.mpgs_session_version = mpgs_response.get("session_version")
                payment.mpgs_order_amount = mpgs_response.get("order_amount")
                payment.mpgs_order_currency = mpgs_response.get("order_currency")
                payment.expiry_datetime = mpgs_response['timeout']

                launch_path = reverse(
                    'frontend:mastercard_checkout', args=[payment.ref_id]
                )
                payment.payment_url = self.request.build_absolute_uri(launch_path)
                payment.save()

                checkout_script_url = getattr(settings, "MPGS_CHECKOUT_SCRIPT_URL", None)
                merchant_name = getattr(settings, "MPGS_MERCHANT_NAME", "")
                merchant_url = getattr(settings, "MPGS_MERCHANT_URL", "")
                if not merchant_url:
                    merchant_url = self.request.build_absolute_uri('/')

                orders_url = self.request.build_absolute_uri(
                    reverse('frontend:esim_orders')
                )

                self.response_data = {
                    "status": True,
                    "message": "Payment created successfully.",
                    "data": serializer.data,
                    "mastercard": {
                        "session_id": str(payment.gateway_transaction_id),
                        "session_version": payment.mpgs_session_version,
                        "success_indicator": payment.mpgs_success_indicator,
                        "checkout_script_url": checkout_script_url,
                        "merchant_name": merchant_name,
                        "merchant_url": merchant_url,
                        "order_amount": (
                            f"{payment.mpgs_order_amount:.2f}"
                            if payment.mpgs_order_amount is not None
                            else ""
                        ),
                        "order_currency": payment.mpgs_order_currency or "",
                        "orders_url": orders_url,
                    },
                }
            else:
                raise serializers.ValidationError({"status": False, "message": mpgs_response.get("message")})
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

    @extend_schema(
        tags=["Payments"],
        summary="Check payment status",
        description="Retrieve the latest status for the payment identified by the reference ID.",
        parameters=[
            OpenApiParameter(
                "ref_id",
                OpenApiTypes.UUID,
                OpenApiParameter.PATH,
                description="The payment reference identifier returned during creation.",
            )
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=PaymentStatusResponseSerializer,
                description="Payment status retrieved successfully.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Unsupported payment gateway or gateway error.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Payment not found for the provided reference ID.",
            ),
        },
    )
    def get(self, request, ref_id):
        try:
            payment = Payment.objects.get(ref_id=ref_id)
        except Payment.DoesNotExist:
            return Response({"status": False, "message": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        if payment.payment_gateway in ('HyperPayMPGS', 'MastercardHostedCheckout'):
            status_response = get_mastercard_payment_status(str(payment.ref_id))
            payment = _apply_mastercard_status(payment, status_response)

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


class MastercardCheckoutCallbackView(APIView):
    """Handle browser returns from Mastercard Hosted Checkout."""

    permission_classes = [AllowAny]

    def _get_payload(self, request):
        if request.method == "POST":
            return request.data
        return request.query_params

    def _process_callback(self, payload):
        order_id = (
            payload.get("orderId")
            or payload.get("order_id")
            or payload.get("order")
            or payload.get("reference")
        )

        if order_id:
            order_id = str(order_id)
        else:
            return Response(
                {"status": False, "message": "Missing order reference."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = Payment.objects.get(ref_id=order_id)
        except Payment.DoesNotExist:
            return Response(
                {"status": False, "message": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        result_indicator = payload.get("resultIndicator") or payload.get("result_indicator")
        session_id = payload.get("sessionId") or payload.get("session_id") or payload.get("session")

        if session_id and session_id != payment.gateway_transaction_id:
            payment.gateway_transaction_id = session_id
            payment.save(update_fields=["gateway_transaction_id"])

        indicator_matched = None
        if result_indicator:
            if payment.mpgs_success_indicator:
                indicator_matched = result_indicator == payment.mpgs_success_indicator
            else:
                indicator_matched = True

        status_response = None

        if indicator_matched is not False:
            status_response = get_mastercard_payment_status(str(payment.ref_id))
            payment = _apply_mastercard_status(payment, status_response)
        else:
            if payment.status != "FAILED":
                payment.status = "FAILED"
                payment.save(update_fields=["status"])

        if payment.payment_gateway not in ("HyperPayMPGS", "MastercardHostedCheckout"):
            message = "Payment recorded, but gateway mismatch detected."
        elif indicator_matched is False:
            message = "Payment verification failed because the result indicator did not match."
        elif payment.status == "COMPLETED":
            message = "Payment completed successfully."
        elif payment.status == "PENDING":
            message = "Payment is pending confirmation."
        else:
            message = "Payment verification failed."

        http_status = status.HTTP_200_OK
        if indicator_matched is False or payment.status == "FAILED":
            http_status = status.HTTP_400_BAD_REQUEST
        elif payment.status == "PENDING":
            http_status = status.HTTP_202_ACCEPTED

        response_data = {
            "status": payment.status == "COMPLETED",
            "message": message,
            "data": {
                "ref_id": payment.ref_id,
                "status": payment.status,
                "amount": payment.price,
                "currency": payment.currency,
                "payment_gateway": payment.payment_gateway,
                "transaction_id": payment.gateway_transaction_id,
                "indicator_matched": indicator_matched,
            },
        }

        if status_response is not None:
            response_data["gateway_response"] = {
                "status": status_response.get("status"),
                "payment_method": status_response.get("payment_method"),
            }

        return Response(response_data, status=http_status)

    @extend_schema(
        tags=["Payments"],
        summary="Handle Mastercard Hosted Checkout callback (GET)",
        description=(
            "Process the query parameters returned by Mastercard Hosted Checkout and "
            "update the associated payment."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=MastercardCallbackResponseSerializer,
                description="Payment verified successfully.",
            ),
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                response=MastercardCallbackResponseSerializer,
                description="Payment is still pending confirmation.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=MastercardCallbackResponseSerializer,
                description="Payment verification failed.",
            ),
        },
    )
    def get(self, request):
        return self._process_callback(self._get_payload(request))

    @extend_schema(
        tags=["Payments"],
        summary="Handle Mastercard Hosted Checkout callback (POST)",
        description=(
            "Process the form payload returned by Mastercard Hosted Checkout and "
            "update the associated payment."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=MastercardCallbackResponseSerializer,
                description="Payment verified successfully.",
            ),
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                response=MastercardCallbackResponseSerializer,
                description="Payment is still pending confirmation.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=MastercardCallbackResponseSerializer,
                description="Payment verification failed.",
            ),
        },
    )
    def post(self, request):
        return self._process_callback(self._get_payload(request))


class UpdatePendingPaymentsView(APIView):
    """
    Checks and updates the status of all pending payments in the last 48 hours.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Payments"],
        summary="Refresh pending payments",
        description=(
            "Check every payment that has been pending in the last 48 hours and "
            "synchronise its status with the configured payment gateway."
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=PendingPaymentsResponseSerializer,
                description="Pending payments processed.",
            ),
        },
    )
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
            if payment.payment_gateway in ("HyperPayMPGS", "MastercardHostedCheckout"):
                status_response = get_mastercard_payment_status(str(payment.ref_id))
                # Ensure status_response is a dict before using .get()
                if isinstance(status_response, list):
                    if status_response:
                        status_response = status_response[0]
                    else:
                        status_response = {}
                payment = _apply_mastercard_status(payment, status_response)

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
