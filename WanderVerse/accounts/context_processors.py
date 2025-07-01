from django.conf import settings

def firebase_config(request):
    """
    Context processor that adds Firebase configuration to the template context.
    """
    config = settings.FIREBASE_CONFIG
    
    return {
        'FIREBASE_CONFIG': {
            'apiKey': config.get('apiKey', ''),
            'authDomain': config.get('authDomain', ''),
            'projectId': config.get('projectId', ''),
            'storageBucket': config.get('storageBucket', ''),
            'messagingSenderId': config.get('messagingSenderId', ''),
            'appId': config.get('appId', '')
        }
    } 