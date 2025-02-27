import urllib.request, urllib.error, urllib.parse
import hmac
import hashlib
import json
import collections
import requests
from django.conf import settings
from datetime import datetime, timedelta, timezone


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


def create_tap_payment(amount, currency, customer_email, reference_id, description):
    """
    Creates a payment charge in TapPayments.
    """
    url = f"{settings.TAP_API_BASE_URL}/charges"
    headers = {
        "Authorization": f"Bearer {settings.TAP_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "amount": float(amount),
        "currency": currency,
        "customer": {
            "email": customer_email
        },
        "source": {
            "id": "src_all"  # This allows multiple payment methods like card, Apple Pay, etc.
        },
        "redirect": {
            "url": settings.TAP_REDIRECT_URL  # Redirect after payment
        },
        "reference": {
            "transaction": reference_id
        },
        "description": description
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        if "id" in data:
            return {
                "status": True,
                "payment_id": data["id"],
                "checkout_url": data["transaction"]["url"],  # URL to redirect user to complete payment
                "timeout": get_payment_expiry(data)  # URL to redirect user to complete payment
            }
        return {"status": False, "message": "Failed to create payment charge."}
    except requests.RequestException as e:
        return {"status": False, "message": f"Error creating payment: {str(e)}"}


def get_tap_payment_status(payment_id):
    """
    Fetches the status of a TapPayments charge.
    """
    url = f"{settings.TAP_API_BASE_URL}/charges/{payment_id}"
    headers = {
        "Authorization": f"Bearer {settings.TAP_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(data.get("status"))

        return {
            "status": data.get("status"),
            "amount": data.get("amount"),
            "currency": data.get("currency"),
            "customer_email": data.get("customer", {}).get("email"),
            "payment_method": data.get("source", {}).get("type"),
            "created": data.get("created"),
        }
    except requests.RequestException as e:
        return {"status": "ERROR", "message": str(e)}


def get_payment_expiry(response_data):
    try:
        # Extract expiry details
        expiry_period = response_data["transaction"]["expiry"]["period"]  # 30 (minutes)
        expiry_type = response_data["transaction"]["expiry"]["type"]  # "MINUTE"
        created_timestamp = int(response_data["transaction"]["created"]) // 1000  # Convert from ms to seconds

        # Convert timestamp to datetime
        created_datetime = datetime.fromtimestamp(created_timestamp, timezone.utc)

        # Determine expiry time based on type
        if expiry_type == "MINUTE":
            expiry_datetime = created_datetime + timedelta(minutes=expiry_period)
        elif expiry_type == "HOUR":
            expiry_datetime = created_datetime + timedelta(hours=expiry_period)
        elif expiry_type == "DAY":
            expiry_datetime = created_datetime + timedelta(days=expiry_period)
        else:
            expiry_datetime = created_datetime  # Default to created time if unknown

        return expiry_datetime

    except KeyError as e:
        print(f"Missing key in response: {e}")
        return None