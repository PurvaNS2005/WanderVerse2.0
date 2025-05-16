import requests
import os
# from datetime import datetime, timedelta # No longer needed for offers
import json

CLIENT_ID = os.getenv("AMADEUS_API_KEY")
CLIENT_SECRET = os.getenv("AMADEUS_SECRET")

def get_amadeus_token():
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Error fetching Amadeus token: {response.status_code} - {response.text}")
        return None

def get_city_code(city_name, token):
    if not token: return None
    url = "https://test.api.amadeus.com/v1/reference-data/locations"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"keyword": city_name, "subType": "CITY"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json().get("data", [])
        if data:
            print(f"--- Amadeus City Code API Response for {city_name} ---")
            print(json.dumps(data, indent=2))
            print("--- End of City Code API Response ---")
            return data[0].get("iataCode")
    else:
        print(f"Error fetching city code: {response.status_code} - {response.text}")
    return None

def get_hotels_in_city(city_code, token, radius=20):
    """
    Fetches a list of hotels within a given city from Amadeus.
    """
    if not token or not city_code: # Handles None or empty string for city_code
        print(f"Skipping get_hotels_in_city: Missing token or city_code. Token present: {bool(token)}, City Code: '{city_code}'")
        return {"hotels": [], "meta": None} # Return a dict with hotels and meta
    
    url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "cityCode": city_code,
        "radius": radius,
        "radiusUnit": "KM"
    }
    
    print(f"Fetching hotels for city code '{city_code}' with radius {radius}km using params: {params}")
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        raw_data = response.json()
        # Ensure we print the full raw_data to inspect for any pagination clues
        print(f"--- Amadeus Hotels by City API Response (City: {city_code}) ---")
        print(json.dumps(raw_data, indent=2))
        print("--- End of Hotels by City API Response ---")
        hotels_list = raw_data.get("data", [])
        meta = raw_data.get("meta") # Attempt to get metadata, might be None
        return {"hotels": hotels_list, "meta": meta}
    else:
        print(f"Error fetching hotels by city: {response.status_code} - {response.text}")
        # Log the URL and params that caused the error for easier debugging
        print(f"Failed URL: {response.url}")
        print(f"Failed Params: {params}")
    return {"hotels": [], "meta": None} # Return a dict with hotels and meta

# Removed get_hotel_offers function as per user request