import os
import requests

AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_SECRET = os.getenv("AMADEUS_SECRET")

def get_amadeus_token():
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_API_KEY,
        "client_secret": AMADEUS_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(url, data=payload, headers=headers)
    r.raise_for_status()  # Optional: raise error if request fails
    return r.json()["access_token"]

def get_points_of_interest(city_lat, city_lon):
    token = get_amadeus_token()
    url = "https://test.api.amadeus.com/v1/reference-data/locations/pois"
    params = {
        "latitude": city_lat,
        "longitude": city_lon,
        "radius": 10
    }
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, params=params, headers=headers)
    r.raise_for_status()
    return r.json().get("data", [])

def get_hotels(city_lat, city_lon):
    token = get_amadeus_token()
    url = "https://test.api.amadeus.com/v1/shopping/hotel-offers"
    params = {
        "latitude": city_lat,
        "longitude": city_lon,
        "radius": 5,
        "radiusUnit": "KM"
    }
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, params=params, headers=headers)
    r.raise_for_status()
    return r.json().get("data", [])
