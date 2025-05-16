import requests
import os

API_KEY = os.getenv("GEOAPIFY_API")

def get_pois(lat, lon, category):
    url = "https://api.geoapify.com/v2/places"
    params = {
        "categories": category,
        "filter": f"circle:{lon},{lat},10000",
        "limit": 20,
        "apiKey": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("features", [])
