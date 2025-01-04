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


def fetch_esim_plan_details(package_code):
    """
    Fetch plan details from the eSIM API using the package code.
    """
    url = esim_host + "/api/v1/open/package/list"
    headers = {"RT-AccessCode": api_token}
    params = {"packageCode": package_code}

    try:
        response = requests.post(url, json=params, headers=headers)
        response.raise_for_status()  # Raise an error for non-200 responses
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Error fetching eSIM plan details: {e}")
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
        data = response.json().get('obj', {}) 
        return data.get('orderNo')
    except requests.RequestException as e:
        print(f"Error ordering eSIM plan: {e}")
        return None