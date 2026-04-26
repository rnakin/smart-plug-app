"""
Firebase Admin SDK configuration for FCM push notifications.
"""
import os
import logging
import firebase_admin
from firebase_admin import credentials

logger = logging.getLogger(__name__)

_firebase_app = None


def get_firebase_app():
    """
    Initialize and return the Firebase Admin app singleton.
    """
    global _firebase_app
    
    if _firebase_app is not None:
        return _firebase_app
    
    project_id = os.environ.get('FIREBASE_PROJECT_ID')
    private_key_id = os.environ.get('FIREBASE_PRIVATE_KEY_ID')
    private_key = os.environ.get('FIREBASE_PRIVATE_KEY')
    client_email = os.environ.get('FIREBASE_CLIENT_EMAIL')
    client_id = os.environ.get('FIREBASE_CLIENT_ID')
    
    if not all([project_id, private_key_id, private_key, client_email]):
        logger.warning('Firebase credentials not fully configured - push notifications disabled')
        return None
    
    try:
        private_key = private_key.replace('\\n', '\n')
        
        cred_dict = {
            'type': 'service_account',
            'project_id': project_id,
            'private_key_id': private_key_id,
            'private_key': private_key,
            'client_email': client_email,
            'client_id': client_id,
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
            'client_x509_cert_url': f'https://www.googleapis.com/robot/v1/metadata/x509/{client_email.replace("@", "%40")}',
            'universe_domain': 'googleapis.com',
        }
        
        cred = credentials.Certificate(cred_dict)
        _firebase_app = firebase_admin.initialize_app(cred)
        
        logger.info('Firebase Admin SDK initialized successfully')
        return _firebase_app
        
    except Exception as e:
        logger.error(f'Failed to initialize Firebase Admin SDK: {e}')
        return None


def is_firebase_configured():
    """
    Check if Firebase is properly configured.
    """
    return get_firebase_app() is not None
