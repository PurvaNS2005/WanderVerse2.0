from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from .firebase_auth import FirebaseAuth
import logging

logger = logging.getLogger(__name__)

class FirebaseAuthMiddleware:
    """
    Middleware for Firebase authentication.
    Checks if the user is authenticated via Firebase for routes that require authentication.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of URLs that don't require authentication
        PUBLIC_URLS = [
            reverse('accounts:verify_token'),
            reverse('accounts:sign_out'),
            reverse('accounts:get_csrf_token'),
            '/',  # Homepage
            '/static/',  # Static files
        ]
        
        # Check if the current URL is public and doesn't need auth
        path_is_public = any(request.path.startswith(url) for url in PUBLIC_URLS)
        if path_is_public:
            return self.get_response(request)
            
        # Check if user is authenticated
        if not request.session.get('user_id'):
            if request.path.startswith('/api/'):
                return JsonResponse({'error': 'Authentication required'}, status=401)
            messages.warning(request, 'Please sign in to access this page')
            return redirect('/')
            
        return self.get_response(request) 