"""
Web Push Notification Service (VAPID-based for browsers).
Used in addition to FCM for web clients that don't have FCM tokens.
"""
import os
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_vapid_public_key():
    """
    Get the VAPID public key for web push.
    Generate keys at: https://web-push-codelab.glitch.me/
    or using: npx web-push generate-vapid-keys
    """
    return os.environ.get('VAPID_PUBLIC_KEY')


def get_vapid_private_key():
    """
    Get the VAPID private key for web push.
    """
    return os.environ.get('VAPID_PRIVATE_KEY')


def get_vapid_admin_email():
    """
    Get the admin email for VAPID.
    """
    return os.environ.get('VAPID_ADMIN_EMAIL', 'admin@example.com')


def is_webpush_configured():
    """
    Check if VAPID keys are configured for web push.
    """
    return bool(get_vapid_public_key() and get_vapid_private_key())


WEBPUSH_CONFIG = {
    'vapid_public_key': get_vapid_public_key(),
    'is_configured': is_webpush_configured(),
}
