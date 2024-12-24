import requests
from decouple import config

def fetch_esim_plan_details(package_code):
    """
    Fetch plan details from the eSIM API using the package code.
    """
    esim_host = config('ESIMACCESS_HOST')
    api_token = config('ESIMACCESS_ACCESS_CODE')
    
    url = esim_host + "/api/v1/open/package/details"
    headers = {"RT-AccessCode": api_token}
    params = {"packageCode": package_code}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for non-200 responses
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Error fetching eSIM plan details: {e}")
        return None