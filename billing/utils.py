import urllib.request, urllib.error, urllib.parse
import hmac
import hashlib
import json
import logging
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import requests
from django.conf import settings
from datetime import datetime, timedelta, timezone


logger = logging.getLogger(__name__)


class FXConversionError(Exception):
    """Raised when currency conversion fails."""


def _to_decimal(amount):
    try:
        if isinstance(amount, Decimal):
            return amount
        return Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise FXConversionError("Invalid amount provided for currency conversion.") from exc


def convert_currency(amount, source_currency, target_currency):
    """Convert ``amount`` from ``source_currency`` to ``target_currency`` using a static USD↔SAR rate.

    Supported pairs:
    - USD → SAR (multiply by FX_USD_SAR_RATE)
    - SAR → USD (divide by FX_USD_SAR_RATE)
    Other pairs are not supported.
    """

    decimal_amount = _to_decimal(amount)
    source = (source_currency or "").upper()
    target = (target_currency or "").upper()

    logger.info("[FX] Preparing conversion: amount=%s, source=%s, target=%s", decimal_amount, source, target)
    print(f"[FX] Preparing conversion: amount={decimal_amount}, source={source}, target={target}")

    if not source or not target:
        raise FXConversionError("Source and target currency codes are required for conversion.")

    if source == target:
        logger.info("[FX] Source and target currency identical; skipping conversion.")
        print("[FX] Source and target currency identical; skipping conversion.")
        return decimal_amount

    # Read static USD↔SAR rate from settings; default to '3.80'
    rate_raw = getattr(settings, "FX_USD_SAR_RATE", "3.80")
    try:
        rate = Decimal(str(rate_raw))
    except (InvalidOperation, TypeError, ValueError) as exc:
        logger.error("[FX] Invalid configured USD↔SAR rate: %s", rate_raw)
        print(f"[FX] Invalid configured USD↔SAR rate: {rate_raw}")
        raise FXConversionError("Configured USD↔SAR rate is invalid.") from exc

    if rate <= 0:
        raise FXConversionError("Configured USD↔SAR rate must be greater than zero.")

    if source == "USD" and target == "SAR":
        converted_amount = decimal_amount * rate
    elif source == "SAR" and target == "USD":
        converted_amount = decimal_amount / rate
    else:
        raise FXConversionError(
            f"Unsupported currency conversion: {source}→{target}. Only USD↔SAR is supported."
        )

    logger.info("[FX] Conversion result: %s %s", converted_amount, target)
    print(f"[FX] Conversion result: {converted_amount} {target}")

    return converted_amount


class CoinPayments():
    def __init__(self, publicKey, privateKey, ipn_url):
        self.publicKey = publicKey
        self.privateKey = privateKey
        self.ipn_url = ipn_url
        self.format = 'json'
        self.version = 1
        self.url = 'https://www.coinpayments.net/api.php'

    def createHmac(self, **params):
        """ Generate an HMAC based upon the url arguments/parameters
            
            We generate the encoded url here and return it to Request because
            the hmac on both sides depends upon the order of the parameters, any
            change in the order and the hmacs wouldn't match
        """
        encoded = urllib.parse.urlencode(params).encode('utf-8')
        return encoded, hmac.new(bytearray(self.privateKey, 'utf-8'), encoded, hashlib.sha512).hexdigest()

    def Request(self, request_method, **params):
        """ The basic request that all API calls use
            the parameters are joined in the actual api methods so the parameter
            strings can be passed and merged inside those methods instead of the 
            request method. The final encoded URL and HMAC are generated here
        """
        encoded, sig = self.createHmac(**params)

        headers = {'hmac': sig}

        if request_method == 'get':
            req = urllib.request.Request(self.url, headers=headers)
        elif request_method == 'post':
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            req = urllib.request.Request(self.url, data=encoded, headers=headers)

        try:
            response      = urllib.request.urlopen(req)
            status_code   = response.getcode()
            response_body = response.read()

            response_body_decoded = json.loads(response_body) #decode Json to dictionary

            response_body_decoded.update(response_body_decoded['result']) #clean up dictionary, flatten "result" key:value pairs to parent dictionary
            response_body_decoded.pop('result', None) #remove the flattened dictionary
            
        except urllib.error.HTTPError as e:
            status_code   = e.getcode()
            response_body = e.read()

        return response_body_decoded

    def createTransaction(self, params=None):
        """ Creates a transaction to give to the purchaser
            https://www.coinpayments.net/apidoc-create-transaction
        """
        params.update({'cmd':'create_transaction',
                       'ipn_url':self.ipn_url,
                       'key':self.publicKey,
                       'version': self.version,
                       'format': self.format}) 
        return self.Request('post', **params)

    def getBasicInfo(self, params=None):
        """Gets merchant info based on API key (callee)
           https://www.coinpayments.net/apidoc-get-basic-info
        """
        params.update({'cmd':'get_basic_info',
                       'key':self.publicKey,
                       'version': self.version,
                       'format': self.format})
        return self.Request('post', **params)

    def getTransactionInfo(self, params=None):
        """Get transaction info
                       https://www.coinpayments.net/apidoc-get-tx-info
        """
       
        params.update({'cmd':'get_tx_info',
                       'key':self.publicKey,
                       'version': self.version,
                       'format': self.format})
        return self.Request('post', **params)
    
    def rates(self, params=None):
        """Gets current rates for currencies
           https://www.coinpayments.net/apidoc-rates 
        """
        params.update({'cmd':'rates',
                       'key':self.publicKey,
                       'version': self.version,
                       'format': self.format})
        return self.Request('post', **params)

    def balances(self, params=None):
        """Get current wallet balances
            https://www.coinpayments.net/apidoc-balances
        """
        params.update({'cmd':'balances',
                       'key':self.publicKey,
                       'version': self.version,
                       'format': self.format})
        return self.Request('post', **params)

    def getDepositAddress(self, params=None):
        """Get address for personal deposit use
           https://www.coinpayments.net/apidoc-get-deposit-address
        """
        params.update({'cmd':'get_deposit_address',
                       'key':self.publicKey,
                       'version': self.version,
                       'format': self.format})
        return self.Request('post', **params)

    def getCallbackAddress(self, params=None):
        """Get a callback address to recieve info about address status
           https://www.coinpayments.net/apidoc-get-callback-address 
        """
        params.update({'cmd':'get_callback_address',
                       'ipn_url':self.ipn_url,
                       'key':self.publicKey,
                       'version': self.version,
                       'format': self.format})
        return self.Request('post', **params)

    def createTransfer(self, params=None):
        """Not really sure why this function exists to be honest, it transfers
            coins from your addresses to another account on coinpayments using
            merchant ID
           https://www.coinpayments.net/apidoc-create-transfer
        """
        params.update({'cmd':'create_transfer',
                       'key':self.publicKey,
                       'version': self.version,
                       'format': self.format})
        return self.Request('post', **params)

    def createWithdrawal(self, params=None):
        """Withdraw or masswithdraw(NOT RECOMMENDED) coins to a specified address,
        optionally set a IPN when complete.
            https://www.coinpayments.net/apidoc-create-withdrawal
        """
        params.update({'cmd':'create_withdrawal',
                        'key':self.publicKey,
                        'version': self.version,
                        'format': self.format})
        return self.Request('post', **params)

    def convertCoins(self, params=None):
        """Convert your balances from one currency to another
            https://www.coinpayments.net/apidoc-convert 
        """
        params.update({'cmd':'convert',
                        'key':self.publicKey,
                        'version': self.version,
                        'format': self.format})
        return self.Request('post', **params)

    def getWithdrawalHistory(self, params=None):
        """Get list of recent withdrawals (1-100max)
            https://www.coinpayments.net/apidoc-get-withdrawal-history 
        """
        params.update({'cmd':'get_withdrawal_history',
                        'key':self.publicKey,
                        'version': self.version,
                        'format': self.format})
        return self.Request('post', **params)

    def getWithdrawalInfo(self, params=None):
        """Get information about a specific withdrawal based on withdrawal ID
            https://www.coinpayments.net/apidoc-get-withdrawal-info
        """
        params.update({'cmd':'get_withdrawal_info',
                        'key':self.publicKey,
                        'version': self.version,
                        'format': self.format})
        return self.Request('post', **params)

    def getConversionInfo(self, params=None):
        """Get information about a specific withdrawal based on withdrawal ID
            https://www.coinpayments.net/apidoc-get-conversion-info
        """
        params.update({'cmd':'get_conversion_info',
                        'key':self.publicKey,
                        'version': self.version,
                        'format': self.format})
        return self.Request('post', **params)


def _mpgs_base_url():
    return settings.MPGS_API_BASE_URL.rstrip('/')


def _mpgs_auth():
    username = f"merchant.{settings.MPGS_MERCHANT_ID}"
    password = settings.MPGS_API_PASSWORD
    return (username, password)


def create_mpgs_checkout(
    amount,
    currency,
    customer_email,
    reference_id,
    description=None,
):
    """Deprecated wrapper kept for backwards compatibility."""
    return initiate_mastercard_checkout(amount, currency, customer_email, reference_id, description)


def initiate_mastercard_checkout(
    amount,
    currency,
    customer_email,
    reference_id,
    description=None,
):
    """Create a hosted checkout session using Mastercard Hosted Checkout (MPGS)."""

    logger.info(
        "[Mastercard Checkout] Initiating checkout: amount=%s, currency=%s, email=%s, reference=%s",
        amount,
        currency,
        customer_email,
        reference_id,
    )
    print(
        f"[Mastercard Checkout] Initiating checkout: amount={amount}, currency={currency}, "
        f"email={customer_email}, reference={reference_id}"
    )

    try:
        order_amount = _to_decimal(amount)
    except FXConversionError as exc:
        logger.error("[Mastercard Checkout] Invalid amount provided: %s", exc)
        print(f"[Mastercard Checkout] Invalid amount provided: {exc}")
        return {
            "status": False,
            "message": "Invalid amount supplied for Mastercard checkout.",
        }

    currency_code = (currency or "USD").upper()

    # Mastercard now supports USD directly, so we only convert if the currency is neither USD nor SAR
    if currency_code not in ("USD", "SAR"):
        try:
            order_amount = convert_currency(order_amount, currency_code, "SAR")
            currency_code = "SAR"
        except FXConversionError as exc:
            logger.error(
                "[Mastercard Checkout] Currency conversion from %s failed: %s",
                currency_code,
                exc,
            )
            print(
                f"[Mastercard Checkout] Currency conversion from {currency_code} failed: {exc}"
            )
            return {
                "status": False,
                "message": "Unable to convert payment amount to SAR for Mastercard checkout.",
            }

    order_amount = order_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    logger.info(
        "[Mastercard Checkout] Prepared order amount: %s %s for reference %s",
        order_amount,
        currency_code,
        reference_id,
    )
    print(
        f"[Mastercard Checkout] Prepared order amount: {order_amount} {currency_code} for reference {reference_id}"
    )

    url = (
        f"{_mpgs_base_url()}/api/rest/version/{settings.MPGS_API_VERSION}/"
        f"merchant/{settings.MPGS_MERCHANT_ID}/session"
    )

    operation = getattr(settings, "MPGS_INTERACTION_OPERATION", "AUTHORIZE") or "AUTHORIZE"
    operation = str(operation).strip().upper()
    interaction_payload = {
        "operation": operation,
        "returnUrl": settings.MPGS_RETURN_URL,
    }

    merchant_name = getattr(settings, "MPGS_MERCHANT_NAME", "")
    merchant_url = getattr(settings, "MPGS_MERCHANT_URL", "")

    if not merchant_url:
        return_url = getattr(settings, "MPGS_RETURN_URL", "")
        if return_url:
            parsed_return = urllib.parse.urlsplit(return_url)
            if parsed_return.scheme and parsed_return.netloc:
                merchant_url = f"{parsed_return.scheme}://{parsed_return.netloc}"

    merchant_details = {}
    if merchant_name:
        merchant_details["name"] = merchant_name
    if merchant_url:
        merchant_details["url"] = merchant_url

    if merchant_details:
        interaction_payload["merchant"] = merchant_details

    order_description = None
    if description:
        order_description = str(description).strip()
        if order_description:
            order_description = order_description[:250]

    payload = {
        "apiOperation": "INITIATE_CHECKOUT",
        "interaction": interaction_payload,
        "order": {
            "amount": format(order_amount, ".2f"),
            "currency": currency_code,
            "id": str(reference_id),
        },
        "transaction": {
            "reference": str(reference_id),
        },
        "customer": {
            "email": customer_email,
        },
    }

    if order_description:
        payload["order"]["description"] = order_description

    # Mastercard Hosted Checkout v100 validates that required fields (amount, currency, id)
    # are supplied during INITIATE_CHECKOUT. Optional attributes, such as order.description,
    # may also be provided when supported by your use case.

    sanitized_payload = deepcopy(payload)
    if "session" in sanitized_payload:
        sanitized_payload["session"].pop("authenticationLimit", None)
    logger.info(
        "[Mastercard Checkout] Request payload: %s",
        json.dumps(sanitized_payload, indent=2, sort_keys=True),
    )
    print(
        f"[Mastercard Checkout] Request payload: {json.dumps(sanitized_payload, indent=2, sort_keys=True)}"
    )

    response = None
    data = None

    try:
        response = requests.post(url, json=payload, auth=_mpgs_auth(), timeout=30)

        try:
            data = response.json()
        except ValueError:
            data = None

        if data is None:
            data = {}

        pretty_payload = json.dumps(data, indent=2, sort_keys=True)
        logger.info("[Mastercard Checkout] Session response: %s", pretty_payload)
        print(f"[Mastercard Checkout] Session response: {pretty_payload}")

        response.raise_for_status()

        session_data = data.get("session", {})
        session_id = session_data.get("id")
        session_version = session_data.get("version")
        success_indicator = data.get("successIndicator")

        if session_id and success_indicator:
            expiry = datetime.now(timezone.utc) + timedelta(
                minutes=settings.MPGS_SESSION_TIMEOUT_MINUTES
            )

            logger.info(
                "[Mastercard Checkout] Session created: session_id=%s, success_indicator=%s",
                session_id,
                success_indicator,
            )
            print(
                f"[Mastercard Checkout] Session created: session_id={session_id}, "
                f"success_indicator={success_indicator}"
            )

            return {
                "status": True,
                "payment_id": session_id,
                "session_id": session_id,
                "session_version": session_version,
                "timeout": expiry,
                "success_indicator": success_indicator,
                "order_amount": order_amount,
                "order_currency": currency_code,
                "order_description": order_description,
            }

        message = (
            data.get("error", {}).get("explanation")
            or data.get("result", {}).get("description")
            or data.get("result")
        )
        logger.error(
            "[Mastercard Checkout] Session creation failed: %s | raw=%s",
            message,
            pretty_payload,
        )
        print(
            f"[Mastercard Checkout] Session creation failed: {message} | raw={pretty_payload}"
        )
        return {
            "status": False,
            "message": message or "Failed to create Mastercard checkout session.",
            "raw": data,
        }
    except requests.RequestException as exc:
        if response is None:
            logger.error("[Mastercard Checkout] Session request failed: %s", exc)
            print(f"[Mastercard Checkout] Session request failed before response: {exc}")
        return {"status": False, "message": f"Error creating Mastercard payment: {exc}"}


def get_mpgs_payment_status(order_id):
    """Deprecated wrapper kept for backwards compatibility."""
    return get_mastercard_payment_status(order_id)


def get_mastercard_payment_status(order_id):
    """Fetch the status of a Mastercard order using the order identifier."""

    logger.info("[Mastercard Checkout] Fetching payment status for order_id=%s", order_id)
    print(f"[Mastercard Checkout] Fetching payment status for order_id={order_id}")

    url = (
        f"{_mpgs_base_url()}/api/rest/version/{settings.MPGS_API_VERSION}/"
        f"merchant/{settings.MPGS_MERCHANT_ID}/order/{order_id}"
    )

    response = None
    data = None

    try:
        response = requests.get(url, auth=_mpgs_auth(), timeout=30)

        try:
            data = response.json()
        except ValueError:
            data = None

        if data is None:
            data = {}

        pretty_payload = json.dumps(data, indent=2, sort_keys=True)
        logger.info("[Mastercard Checkout] Order %s status payload: %s", order_id, pretty_payload)
        print(f"[Mastercard Checkout] Order {order_id} status payload: {pretty_payload}")

        response.raise_for_status()

        order_data = data.get("order", {})
        status = order_data.get("status") or data.get("result")
        amount = order_data.get("amount")
        currency = order_data.get("currency")

        transaction = None
        transactions = data.get("transactions")
        if isinstance(transactions, list) and transactions:
            transaction = transactions[-1]

        if transaction is None:
            transaction_data = data.get("transaction")
            if isinstance(transaction_data, list) and transaction_data:
                transaction = transaction_data[-1]
            elif isinstance(transaction_data, dict):
                transaction = transaction_data

        payment_method = None
        if isinstance(transaction, dict):
            payment_method = transaction.get("paymentMethod") or transaction.get(
                "sourceOfFunds", {}
            ).get("type")

        customer_email = order_data.get("customerEmail") or data.get("customer", {}).get("email")

        result = {
            "status": status,
            "amount": amount,
            "currency": currency,
            "customer_email": customer_email,
            "payment_method": payment_method,
            "raw": data,
        }

        logger.info("[Mastercard Checkout] Normalized order status: %s", json.dumps(result, indent=2, sort_keys=True))
        print(
            f"[Mastercard Checkout] Normalized order status: {json.dumps(result, indent=2, sort_keys=True)}"
        )

        return result
    except requests.RequestException as exc:
        if response is None:
            logger.error("[Mastercard Checkout] Order status request failed: %s", exc)
            print(f"[Mastercard Checkout] Order status request failed before response: {exc}")

        return {"status": "ERROR", "message": str(exc)}
