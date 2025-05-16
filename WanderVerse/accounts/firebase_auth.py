from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse
from firebase_admin import auth, credentials, firestore, initialize_app, get_app
import firebase_admin
import os
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

class FirebaseAuth:
    """
    Firebase Authentication and Firestore Database Handler
    """
    _initialized = False
    _db = None

    @classmethod
    def initialize_firebase(cls):
        """Initialize Firebase Admin SDK if not already initialized"""
        if cls._initialized:
            return True
            
        try:
            # Check if Firebase is already initialized
            try:
                get_app()
                cls._initialized = True
                return True
            except ValueError:
                # Firebase not initialized, continue with initialization
                pass

            key_path = settings.FIREBASE_KEY_PATH
            if not os.path.exists(key_path):
                logger.error("Firebase key file not found")
                return False
                
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            cls._initialized = True
            return True
        except Exception as e:
            logger.error(f"Firebase initialization failed: {str(e)}")
            return False

    @classmethod
    def get_db(cls):
        """Get Firestore database instance"""
        if not cls.initialize_firebase():
            return None
        if not cls._db:
            cls._db = firestore.client()
        return cls._db

    @classmethod
    def verify_token(cls, id_token):
        """Verify Firebase ID token"""
        if not cls.initialize_firebase():
            return None
            
        try:
            if not id_token:
                return None
                
            decoded_token = auth.verify_id_token(id_token)
            if not decoded_token:
                return None
                
            return decoded_token
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            return None

    @classmethod
    def get_user_data(cls, uid):
        """Get user data from Firestore"""
        if not cls.initialize_firebase():
            return None
            
        try:
            db = cls.get_db()
            if not db:
                return None
                
            user_ref = db.collection('users').document(uid)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                return user_doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting user data: {str(e)}")
            return None

    @classmethod
    def create_or_update_user(cls, uid, user_data):
        """Create or update user document in Firestore"""
        if not cls.initialize_firebase():
            return False
            
        try:
            db = cls.get_db()
            if not db:
                return False
                
            user_ref = db.collection('users').document(uid)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_ref.update(user_data)
            else:
                user_ref.set(user_data)
            return True
        except Exception as e:
            logger.error(f"Error updating user data: {str(e)}")
            return False

    @classmethod
    def get_firebase_config(cls):
        """
        Get Firebase configuration for templates.
        
        Returns:
            dict: Firebase configuration
        """
        try:
            return {'FIREBASE_CONFIG': settings.FIREBASE_CONFIG}
        except Exception as e:
            logger.error(f"Failed to get Firebase config: {str(e)}")
            return {'FIREBASE_CONFIG': {}}

# Initialize Firebase when module is imported
FirebaseAuth.initialize_firebase() 