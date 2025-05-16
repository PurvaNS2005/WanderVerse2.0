# trips/utils/osm_utils.py
import overpy

def get_tourist_pois(lat, lon, radius_km=5):
    api = overpy.Overpass()
    radius_m = radius_km * 1000
    query = f"""
    [out:json];
    (
      node["tourism"="attraction"](around:{radius_m},{lat},{lon});
      way["tourism"="attraction"](around:{radius_m},{lat},{lon});
      relation["tourism"="attraction"](around:{radius_m},{lat},{lon});
    );
    out center;
    """

    try:
        result = api.query(query)
        pois = []
        for node in result.nodes:
            pois.append({
                "name": node.tags.get("name", "Unnamed"),
                "lat": node.lat,
                "lon": node.lon,
                "type": node.tags.get("tourism", "attraction")
            })
        return pois
    except Exception as e:
        print(f"Error fetching POIs: {e}")
        return []
