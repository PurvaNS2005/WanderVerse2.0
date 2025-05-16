import requests
import os

API_KEY = os.getenv("GEODB_API")

def get_city_coordinates(city_name):
    url = "https://wft-geo-db.p.rapidapi.com/v1/geo/cities"
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "wft-geo-db.p.rapidapi.com"
    }
    params = {
        "namePrefix": city_name,
        "limit": 1,
        "sort": "-population"
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data["data"]:
        city = data["data"][0]
        return {
            "lat": city["latitude"],
            "lon": city["longitude"],
            "full_name": f"{city['city']}, {city['countryCode']}"
        }
    return None
