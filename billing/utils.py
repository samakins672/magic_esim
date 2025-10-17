import urllib.request, urllib.error, urllib.parse
import hmac
import hashlib
import json
import collections
import logging
import requests
from django.conf import settings
from datetime import datetime, timedelta, timezone


logger = logging.getLogger(__name__)


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


def create_mpgs_checkout(amount, currency, customer_email, reference_id, description):
    """Create a hosted checkout session using HyperPay MPGS."""

    url = (
        f"{_mpgs_base_url()}/api/rest/version/{settings.MPGS_API_VERSION}/"
        f"merchant/{settings.MPGS_MERCHANT_ID}/session"
    )

    payload = {
        "apiOperation": "CREATE_CHECKOUT_SESSION",
        "order": {
            "amount": f"{float(amount):.2f}",
            "currency": currency,
            "id": str(reference_id),
            "description": description,
        },
        "transaction": {
            "reference": str(reference_id),
        },
        "customer": {
            "email": customer_email,
        },
        "interaction": {
            "operation": "PURCHASE",
            "returnUrl": settings.MPGS_RETURN_URL,
        },
    }

    try:
        response = requests.post(url, json=payload, auth=_mpgs_auth())
        response.raise_for_status()
        data = response.json()

        print(
            "[HyperPay MPGS] Checkout response:",
            json.dumps(data, indent=2, sort_keys=True),
        )

        session_id = data.get("session", {}).get("id")
        success_indicator = data.get("successIndicator")

        if session_id and success_indicator:
            checkout_url = settings.MPGS_CHECKOUT_URL.rstrip('/')
            checkout_url = (
                f"{checkout_url}?sessionId={session_id}&successIndicator={success_indicator}"
                f"&merchantId={settings.MPGS_MERCHANT_ID}"
            )

            expiry = datetime.now(timezone.utc) + timedelta(
                minutes=settings.MPGS_SESSION_TIMEOUT_MINUTES
            )

            return {
                "status": True,
                "payment_id": session_id,
                "checkout_url": checkout_url,
                "timeout": expiry,
            }

        message = data.get("error", {}).get("explanation") or data.get("result")
        return {"status": False, "message": message or "Failed to create checkout session."}
    except requests.RequestException as exc:
        return {"status": False, "message": f"Error creating payment: {exc}"}


def get_mpgs_payment_status(order_id):
    """Fetch the status of an MPGS order using the order identifier."""

    url = (
        f"{_mpgs_base_url()}/api/rest/version/{settings.MPGS_API_VERSION}/"
        f"merchant/{settings.MPGS_MERCHANT_ID}/order/{order_id}"
    )

    try:
        response = requests.get(url, auth=_mpgs_auth())
        response.raise_for_status()
        data = response.json()

        print(
            "[HyperPay MPGS] Order status response:",
            json.dumps(data, indent=2, sort_keys=True),
        )

        order_data = data.get("order", {})
        status = order_data.get("status") or data.get("result")
        amount = order_data.get("amount")
        currency = order_data.get("currency")

        transaction = None
        if isinstance(data.get("transactions"), list) and data["transactions"]:
            transaction = data["transactions"][-1]
        elif data.get("transaction"):
            transaction = data["transaction"]

        payment_method = None
        if transaction:
            payment_method = transaction.get("paymentMethod") or transaction.get(
                "sourceOfFunds", {}
            ).get("type")

        customer_email = order_data.get("customerEmail") or data.get("customer", {}).get("email")

        return {
            "status": status,
            "amount": amount,
            "currency": currency,
            "customer_email": customer_email,
            "payment_method": payment_method,
            "raw": data,
        }
    except requests.RequestException as exc:
        return {"status": "ERROR", "message": str(exc)}


def _hyperpay_base_url():
    return settings.HYPERPAY_API_BASE_URL.rstrip('/')


def _hyperpay_headers():
    return {
        "Authorization": f"Bearer {settings.HYPERPAY_ACCESS_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def normalize_copy_and_pay_checkout_id(checkout_id):
    """Strip query strings or fragments from a HyperPay checkout identifier."""

    if not checkout_id:
        return checkout_id

    cleaned = urllib.parse.unquote(checkout_id).strip()

    for delimiter in ("?", "#"):
        if delimiter in cleaned:
            cleaned = cleaned.split(delimiter, 1)[0]

    return cleaned


def create_copy_and_pay_checkout(
    amount,
    currency,
    customer_email,
    reference_id,
    description,
    shopper_result_url=None,
):
    """Create a HyperPay Copy & Pay checkout session."""

    if not settings.HYPERPAY_ENTITY_ID or not settings.HYPERPAY_ACCESS_TOKEN:
        return {
            "status": False,
            "message": "HyperPay Copy & Pay is not configured.",
        }

    url = f"{_hyperpay_base_url()}/v1/checkouts"

    payload = {
        "entityId": settings.HYPERPAY_ENTITY_ID,
        "amount": f"{float(amount):.2f}",
        "currency": currency,
        "paymentType": "DB",
        "merchantTransactionId": str(reference_id),
        "customer.email": customer_email,
    }

    if description:
        payload["descriptor"] = description[:127]

    if shopper_result_url or settings.HYPERPAY_RETURN_URL:
        payload["shopperResultUrl"] = shopper_result_url or settings.HYPERPAY_RETURN_URL

    try:
        response = requests.post(url, data=payload, headers=_hyperpay_headers())
        response.raise_for_status()
        data = response.json()

        print(
            "[HyperPay Copy & Pay] Checkout response:",
            json.dumps(data, indent=2, sort_keys=True),
        )

        checkout_id = data.get("id")

        if checkout_id:
            expiry = datetime.now(timezone.utc) + timedelta(
                minutes=settings.HYPERPAY_CHECKOUT_TIMEOUT_MINUTES
            )

            return {
                "status": True,
                "checkout_id": checkout_id,
                "payment_id": checkout_id,
                "timeout": expiry,
                "integrity": data.get("integrity"),
                "raw": data,
            }

        result_message = data.get("result", {}).get("description")
        return {
            "status": False,
            "message": result_message or "Failed to create HyperPay checkout.",
            "raw": data,
        }
    except requests.RequestException as exc:
        return {"status": False, "message": f"Error creating HyperPay payment: {exc}"}


def get_copy_and_pay_payment_status(checkout_id, resource_path=None):
    """Fetch the payment status for a Copy & Pay checkout."""

    normalized_checkout_id = normalize_copy_and_pay_checkout_id(checkout_id)
    normalized_resource_path = (resource_path or "").strip()

    if normalized_resource_path:
        normalized_resource_path = normalized_resource_path.lstrip("/")
        url = f"{_hyperpay_base_url()}/{normalized_resource_path}"

        if not normalized_checkout_id:
            segments = [segment for segment in normalized_resource_path.split("/") if segment]
            if "checkouts" in segments:
                index = segments.index("checkouts")
                if index + 1 < len(segments):
                    normalized_checkout_id = normalize_copy_and_pay_checkout_id(
                        segments[index + 1]
                    )
    else:
        if not normalized_checkout_id:
            return {"status": "ERROR", "message": "Missing HyperPay checkout identifier."}
        url = f"{_hyperpay_base_url()}/v1/checkouts/{normalized_checkout_id}/payment"
    params = {"entityId": settings.HYPERPAY_ENTITY_ID}

    try:
        if not settings.HYPERPAY_ENTITY_ID or not settings.HYPERPAY_ACCESS_TOKEN:
            return {
                "status": "ERROR",
                "message": "HyperPay Copy & Pay is not configured.",
            }

        response = requests.get(url, params=params, headers=_hyperpay_headers())
        response.raise_for_status()
        data = response.json()

        print(
            "[HyperPay Copy & Pay] Status response:",
            json.dumps(data, indent=2, sort_keys=True),
        )

        log_key = normalized_resource_path or normalized_checkout_id or checkout_id
        logger.info(
            "[HyperPay Copy & Pay] Checkout %s status payload: %s",
            log_key,
            json.dumps(data, indent=2, sort_keys=True),
        )

        result = data.get("result", {})
        result_code = (result.get("code") or "").strip()

        normalized_status = "PENDING"
        if result_code.startswith(("000.000", "000.100")):
            normalized_status = "COMPLETED"
        elif result_code.startswith("000.200"):
            normalized_status = "PENDING"
        elif result_code:
            normalized_status = "FAILED"

        transaction_id = data.get("id") or data.get("ndc")

        return {
            "status": normalized_status,
            "amount": data.get("amount"),
            "currency": data.get("currency"),
            "result_code": result_code,
            "result_description": result.get("description"),
            "transaction_id": transaction_id,
            "raw": data,
        }
    except requests.RequestException as exc:
        return {"status": "ERROR", "message": str(exc)}
