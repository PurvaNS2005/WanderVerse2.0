import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase app only once
cred_path = os.getenv("FIREBASE_KEY_PATH", "firebase/serviceAccountKey.json")
cred = credentials.Certificate(cred_path)

try:
    app = firebase_admin.get_app()
except ValueError:
    app = firebase_admin.initialize_app(cred)

db = firestore.client()

def save_trip(data):
    trips_ref = db.collection('trips')
    trips_ref.add(data)
