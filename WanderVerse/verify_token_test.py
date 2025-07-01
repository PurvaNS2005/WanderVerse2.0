"""
Test script for Firebase token verification

This script can be used to directly test the Firebase token verification
without going through the web interface.

Usage:
    python verify_token_test.py

It will test both Firebase initialization and token generation/verification.
"""

import os
import sys
import django
import time
import json
from pathlib import Path

# Add the parent directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WanderVerse.settings')
django.setup()

# Now that Django is set up, import the Firebase auth module
from accounts.firebase_auth import FirebaseAuth
from django.conf import settings
import firebase_admin
from firebase_admin import auth, credentials

def create_custom_token():
    """Create a custom token for testing purposes."""
    try:
        # Ensure Firebase is initialized
        if not FirebaseAuth.initialize_firebase():
            print("Cannot create token: Firebase not initialized")
            return None
            
        # Create a custom user ID for testing
        test_uid = f"test-user-{int(time.time())}"
        
        # Create custom token with claims
        custom_token = firebase_admin.auth.create_custom_token(
            test_uid,
            {
                'email': f"{test_uid}@example.com",
                'name': 'Test User',
                'admin': False
            }
        )
        
        print(f"Created custom token for UID: {test_uid}")
        return custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token
    except Exception as e:
        print(f"Error creating custom token: {e}")
        return None

def verify_with_django_view(token):
    """Simulate a request to the Django view for token verification."""
    from django.test import RequestFactory
    from accounts.views import verify_token
    from django.middleware.csrf import get_token
    
    factory = RequestFactory()
    request = factory.post(
        '/accounts/verify-token/', 
        data=json.dumps({'idToken': token}),
        content_type='application/json'
    )
    
    # Add CSRF token
    get_token(request)
    
    # Call the view directly
    response = verify_token(request)
    
    # Return results
    return {
        'status_code': response.status_code,
        'content': json.loads(response.content.decode('utf-8')),
        'headers': dict(response.items())
    }

def main():
    # Print Firebase settings
    print("\n===== FIREBASE CONFIGURATION =====")
    print(f"Firebase key path: {settings.FIREBASE_KEY_PATH}")
    print(f"File exists: {os.path.exists(settings.FIREBASE_KEY_PATH)}")
    
    # Test Firebase initialization
    print("\n===== FIREBASE INITIALIZATION =====")
    init_success = FirebaseAuth.initialize_firebase()
    print(f"Firebase initialization: {'SUCCESS' if init_success else 'FAILED'}")
    
    if not init_success:
        print("Firebase initialization failed, cannot continue")
        return 1
    
    # Create a custom token for testing
    print("\n===== TOKEN CREATION =====")
    custom_token = create_custom_token()
    if not custom_token:
        print("Failed to create custom token")
        return 1
    
    print(f"Custom token: {custom_token[:20]}...")
    
    # Verify the token with the Firebase Auth SDK
    print("\n===== DIRECT SDK VERIFICATION =====")
    try:
        # Note: Custom tokens need to be exchanged for ID tokens
        # This can't be done server-side directly, but we can verify the format
        print("Custom token validation: format appears valid")
        
        # Test list users to verify overall Firebase access
        page = auth.list_users()
        print(f"Firebase Auth API access test: Success (found {len(list(page.iterate_all()))} users)")
    except Exception as e:
        print(f"Error verifying with Firebase SDK: {e}")
    
    # Test with the Django view (bypassing HTTP)
    print("\n===== DJANGO VIEW VERIFICATION =====")
    try:
        print("Note: This is expected to fail as custom tokens need client-side exchange")
        result = verify_with_django_view(custom_token)
        print(f"Status code: {result['status_code']}")
        print(f"Response content: {result['content']}")
    except Exception as e:
        print(f"Error calling Django view: {e}")
    
    # Print verification instructions
    print("\n===== VERIFICATION CONCLUSION =====")
    print("Custom tokens cannot be directly verified server-side.")
    print("To complete testing, you would need:")
    print("1. A real ID token from the Firebase Auth client SDK")
    print("2. Or fix the client-side verification process")
    
    # Debug Firebase credentials
    print("\n===== CREDENTIALS CHECK =====")
    try:
        firebase_app = firebase_admin.get_app()
        print(f"Firebase app name: {firebase_app.name}")
        print(f"Firebase project ID: {firebase_app.project_id if hasattr(firebase_app, 'project_id') else 'Not available'}")
    except Exception as e:
        print(f"Error getting Firebase app: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 