#!/usr/bin/env python3
"""Django's command-line utility for administrative tasks."""
import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv("../.env")

def initialize_firebase():
    key_path = os.getenv("FIREBASE_KEY_PATH")
    if key_path is None:
        raise ValueError("FIREBASE_KEY_PATH environment variable is not set.")
    
    if not firebase_admin._apps:  # Prevent multiple initializations
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)

    return firestore.client()

def main():
    db = initialize_firebase()
    print("Firebase initialized successfully!")

    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WanderVerse.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
    


if __name__ == '__main__':
    main()
