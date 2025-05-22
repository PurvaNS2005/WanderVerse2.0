import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime

# Initialize Firebase app only once
cred_path = os.getenv("FIREBASE_KEY_PATH", "firebase/serviceAccountKey.json")
cred = credentials.Certificate(cred_path)

try:
    app = firebase_admin.get_app()
except ValueError:
    app = firebase_admin.initialize_app(cred)

db = firestore.client()

def save_trip(user_id, city_name, start_date, end_date, itinerary):
    """Save a trip to Firestore with proper data validation"""
    try:
        # Only use the city_name string provided by the view
        if not isinstance(city_name, str) or not city_name.strip():
            raise ValueError("City name must be a non-empty string")
        # Ensure dates are in correct format
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%Y-%m-%d')
        if isinstance(end_date, datetime):
            end_date = end_date.strftime('%Y-%m-%d')
        # Include time in itinerary items and sort by time
        for date, items in itinerary.items():
            for item in items:
                if 'time' not in item:
                    item['time'] = '00:00'  # Default time if not provided
                # Convert time to 24-hour format for sorting
                item['time_24'] = datetime.strptime(item['time'], '%I:%M %p').strftime('%H:%M')
            items.sort(key=lambda x: x['time_24'])  # Sort items by 24-hour time
            for item in items:
                del item['time_24']  # Remove the temporary 24-hour time key
        trip_data = {
            'userId': user_id,
            'city': city_name.strip(),  # Always use the city_name string from the view
            'startDate': start_date,
            'endDate': end_date,
            'itinerary': itinerary,
            'createdAt': firestore.SERVER_TIMESTAMP
        }
        print(f"Saving trip for user {user_id}: {trip_data}")
        trips_ref = db.collection('trips')
        doc_ref = trips_ref.add(trip_data)
        print(f"Trip saved successfully with ID: {doc_ref[1].id}")
        return doc_ref[1].id
    except Exception as e:
        print(f"Error saving trip: {str(e)}")
        raise
