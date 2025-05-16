from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from firebase_admin import auth, firestore
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
import json
import logging
import traceback
from .firebase_auth import FirebaseAuth
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime

logger = logging.getLogger(__name__)

@require_http_methods(["POST"])
@csrf_protect
def verify_token(request):
    """
    Verify Firebase ID token and create a session for the user.
    """
    try:
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON data: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)

        # Get and validate token
        id_token = data.get('idToken')
        if not id_token:
            logger.error("No token provided in request")
            return JsonResponse({
                'status': 'error',
                'message': 'No token provided'
            }, status=400)
        
        # Initialize Firebase
        if not FirebaseAuth.initialize_firebase():
            logger.error("Firebase initialization failed")
            return JsonResponse({
                'status': 'error',
                'message': 'Firebase initialization failed'
            }, status=500)
            
        # Verify token
        decoded_token = FirebaseAuth.verify_token(id_token)
        if not decoded_token:
            logger.error("Token verification failed")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid token'
            }, status=401)
        
        # Extract user info
        try:
            uid = decoded_token.get('uid')
            if not uid:
                logger.error("No UID in decoded token")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid token data'
                }, status=401)

            email = decoded_token.get('email', '')
            name = decoded_token.get('name', '') or decoded_token.get('email', '').split('@')[0]
            picture = decoded_token.get('picture', '')
            
            # Prepare user data
            user_data = {
                'email': email,
                'displayName': name,
                'photoURL': picture,
                'lastLogin': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }
            
            # Update user in Firestore
            if not FirebaseAuth.create_or_update_user(uid, user_data):
                logger.error(f"Failed to create/update user in Firestore: {uid}")
                # Continue with session creation even if Firestore update fails
                logger.warning("Continuing with session creation despite Firestore update failure")
            
            # Set session data
            request.session['uid'] = uid
            request.session['user_email'] = email
            request.session['user_name'] = name
            request.session['user_picture'] = picture
            
            return JsonResponse({
                'status': 'success',
                'message': f'Welcome back, {name}! 🎉',
                'user': {
                    'uid': uid,
                    'email': email,
                    'name': name,
                    'picture': picture
                }
            })
            
        except Exception as e:
            logger.error(f"Error processing user data: {str(e)}\n{traceback.format_exc()}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error processing user data'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Unexpected error in verify_token: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'status': 'error',
            'message': 'Server error occurred'
        }, status=500)

@require_http_methods(["POST"])
@csrf_protect
def sign_out(request):
    """
    Clear the session and sign out the user.
    """
    try:
        request.session.flush()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Sign out error: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'status': 'error',
            'message': 'Server error occurred'
        }, status=500)

@require_http_methods(["GET"])
def profile(request):
    """Render the user's profile page"""
    if not request.session.get('uid'):
        messages.warning(request, 'Please sign in to view your profile')
        return redirect('/')
        
    try:
        # Get user data from Firestore
        user_data = FirebaseAuth.get_user_data(request.session['uid'])
        if not user_data:
            messages.error(request, 'Failed to load profile data')
            return redirect('/')
            
        # Convert Firestore data to dict and ensure all fields exist
        user_data = {
            'uid': request.session['uid'],
            'email': user_data.get('email', request.session.get('user_email', '')),
            'displayName': user_data.get('displayName', request.session.get('user_name', '')),
            'photoURL': user_data.get('photoURL', request.session.get('user_picture', '')),
            'createdAt': user_data.get('createdAt', datetime.now()),
            'isPremium': user_data.get('isPremium', False),
            'tripsPlanned': user_data.get('tripsPlanned', 0),
            'destinationsVisited': user_data.get('destinationsVisited', 0),
            'reviewsCount': user_data.get('reviewsCount', 0),
            'bio': user_data.get('bio', ''),
            'emailNotifications': user_data.get('emailNotifications', True),
            'darkMode': user_data.get('darkMode', False)
        }
            
        # Get recent activities
        recent_activities = get_recent_activities(request.session['uid'])
        
        context = {
            'user_data': user_data,
            'recent_activities': recent_activities
        }
        return render(request, 'accounts/profile.html', context)
    except Exception as e:
        logger.error(f"Error loading profile: {str(e)}")
        messages.error(request, 'An error occurred while loading your profile')
        return redirect('/')

@require_http_methods(["POST"])
def update_profile(request):
    """Update user profile information"""
    if not request.session.get('uid'):
        return JsonResponse({'success': False, 'message': 'Not authenticated'}, status=401)
        
    try:
        data = json.loads(request.body)
        user_data = {
            'display_name': data.get('display_name'),
            'bio': data.get('bio'),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Update user data in Firestore
        success = FirebaseAuth.create_or_update_user(request.session['uid'], user_data)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Failed to update profile'}, status=500)
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return JsonResponse({'success': False, 'message': 'An error occurred'}, status=500)

@require_http_methods(["POST"])
def update_profile_picture(request):
    """Update user's profile picture"""
    if not request.session.get('uid'):
        return JsonResponse({'success': False, 'message': 'Not authenticated'}, status=401)
        
    try:
        if 'profile_picture' not in request.FILES:
            return JsonResponse({'success': False, 'message': 'No file uploaded'}, status=400)
            
        file = request.FILES['profile_picture']
        if not file.content_type.startswith('image/'):
            return JsonResponse({'success': False, 'message': 'Invalid file type'}, status=400)
            
        # Save file to storage
        file_name = f"profile_pictures/{request.session['uid']}/{file.name}"
        path = default_storage.save(file_name, ContentFile(file.read()))
        
        # Get the URL for the saved file
        photo_url = default_storage.url(path)
        
        # Update user data in Firestore
        user_data = {
            'photoURL': photo_url,
            'updatedAt': datetime.utcnow().isoformat()
        }
        success = FirebaseAuth.create_or_update_user(request.session['uid'], user_data)
        
        if success:
            # Update session data
            request.session['user_picture'] = photo_url
            return JsonResponse({
                'success': True, 
                'photoURL': photo_url,
                'message': 'Profile picture updated successfully'
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': 'Failed to update profile picture'
            }, status=500)
    except Exception as e:
        logger.error(f"Error updating profile picture: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'An error occurred while updating profile picture'
        }, status=500)

def get_recent_activities(user_id):
    """Get user's recent activities from Firestore"""
    try:
        db = FirebaseAuth.get_db()
        if not db:
            return []
            
        # Query recent activities
        activities_ref = db.collection('users').document(user_id).collection('activities')
        activities = activities_ref.order_by('timestamp', direction='DESCENDING').limit(5).stream()
        
        return [activity.to_dict() for activity in activities]
    except Exception as e:
        logger.error(f"Error getting recent activities: {str(e)}")
        return []

@ensure_csrf_cookie
def get_csrf_token(request):
    """
    Return a new CSRF token for the frontend.
    """
    response = JsonResponse({'status': 'success', 'message': 'CSRF token set'})
    
    # Set cache control headers to prevent caching
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response
