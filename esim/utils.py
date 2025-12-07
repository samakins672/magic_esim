import requests
from decouple import config
from datetime import timedelta
from django.utils.timezone import now


esim_host = config('ESIMACCESS_HOST')
api_token = config('ESIMACCESS_ACCESS_CODE')

def calculate_expiry_date(duration):
    """
    Calculate the expiry date based on the current time and duration in days.
    """
    return now() + timedelta(days=duration)


def fetch_esim_plan_details(package_code, seller="esimaccess"):
    """
    Fetch plan details from the eSIM API using the package_code.
    The 'seller' parameter determines which provider to query:
      - 'esimaccess': existing POST call
      - 'esimgo': GET call to eSIM-Go
    """
    try:
        if seller.lower() == "esimgo":
            # eSIM-Go flow
            esimgo_host = config("ESIMGO_HOST")
            esimgo_api_key = config("ESIMGO_API_KEY")  # You can set a default in your .env or code

            # Build the GET URL for eSIM-Go
            # Example: https://api.esim-go.com/v2.4/catalogue/bundle/<package_code>?api_key=...
            url = f"{esimgo_host}/catalogue/bundle/{package_code}?api_key={esimgo_api_key}"

            headers = {
                "accept": "application/json",
                "x-api-key": esimgo_api_key
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an error if status_code != 200
            return response.json()

        else:
            # eSIMAccess flow (default)
            esim_host = config("ESIMACCESS_HOST")
            api_token = config("ESIMACCESS_ACCESS_CODE")

            url = f"{esim_host}/api/v1/open/package/list"
            headers = {"RT-AccessCode": api_token}
            payload = {"packageCode": package_code}

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    except requests.RequestException as e:
        # Log or handle the exception as appropriate for your app
        print(f"Error fetching eSIM plan details from {seller}: {e}")
        return None


def order_esim_profile(package_code, ref_id, amount):
    """
    Order new plan from the eSIM API.
    """
    url = esim_host + "/api/v1/open/esim/order"
    headers = {"RT-AccessCode": api_token}
    params = {
        "transactionId": str(ref_id),
        "amount": amount,
        "packageInfoList": [{
            "packageCode": package_code,
            "count": 1,
            "price": amount,
        }]
    }

    try:
        response = requests.post(url, json=params, headers=headers)
        response.raise_for_status()  # Raise an error for non-200 responses
        try:
            payload = response.json() or {}
        except ValueError:
            payload = {}

        obj = payload.get('obj') if isinstance(payload, dict) else None
        if not isinstance(obj, dict):
            print(f"Error ordering eSIM plan: unexpected response body {payload}")
            return None

        return obj.get('orderNo')
    except requests.RequestException as e:
        print(f"Error ordering eSIM plan: {e}")
        return None
