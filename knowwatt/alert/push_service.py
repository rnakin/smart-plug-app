"""
FCM Push Notification Service for KnowWatt alerts.
"""
import logging
from django.utils import timezone
from firebase_admin import messaging
from .models import UserPushToken, AlertEvent

logger = logging.getLogger(__name__)


def send_push_notification(user, title, body, data=None, tokens=None):
    """
    Send a push notification to a user's devices via FCM.
    
    Args:
        user: Django User instance
        title: Notification title
        body: Notification body/message
        data: Optional dict of custom data to include
        tokens: Optional list of specific tokens to send to (if None, sends to all user's tokens)
    
    Returns:
        tuple: (success_count, failure_count)
    """
    from knowwatt.firebase_config import get_firebase_app
    
    app = get_firebase_app()
    if not app:
        logger.warning('Firebase not configured - cannot send push notification')
        return (0, 0)
    
    if tokens is None:
        active_tokens = UserPushToken.objects.filter(
            user=user,
            is_active=True
        ).values_list('token', flat=True)
        tokens = list(active_tokens)
    
    if not tokens:
        logger.info(f'No active push tokens for user {user.username}')
        return (0, 0)
    
    success_count = 0
    failure_count = 0
    
    for token in tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        icon='notification_icon',
                        color='#00f2ff',
                        sound='default',
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                        ),
                    ),
                ),
            )
            
            response = messaging.send(message, app=app)
            logger.info(f'Push sent successfully to token {token[:20]}...: {response}')
            success_count += 1
            
            UserPushToken.objects.filter(token=token).update(last_used_at=timezone.now())
            
        except messaging.UnregisteredError:
            logger.warning(f'Token unregistered, marking inactive: {token[:20]}...')
            UserPushToken.objects.filter(token=token).update(is_active=False)
            failure_count += 1
            
        except Exception as e:
            logger.error(f'Failed to send push to token {token[:20]}...: {e}')
            failure_count += 1
    
    return (success_count, failure_count)


def send_alert_push(alert_event):
    """
    Send a push notification for an AlertEvent.
    
    Args:
        alert_event: AlertEvent instance
    
    Returns:
        bool: True if notification was sent successfully to at least one device
    """
    if alert_event.push_sent:
        logger.info(f'Alert {alert_event.id} already has push sent')
        return True
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    house = alert_event.house
    members = house.members.filter(is_active=True).select_related('user')
    
    total_success = 0
    
    for member in members:
        user = member.user
        success, _ = send_push_notification(
            user=user,
            title=alert_event.title,
            body=alert_event.message,
            data={
                'alert_id': str(alert_event.id),
                'house_id': str(house.id),
                'event_type': alert_event.rule.trigger if alert_event.rule else 'unknown',
                'plug_id': str(alert_event.plug_id) if alert_event.plug_id else '',
                'device_id': str(alert_event.device_id) if alert_event.device_id else '',
            }
        )
        total_success += success
    
    if total_success > 0:
        alert_event.push_sent = True
        alert_event.push_sent_at = timezone.now()
        alert_event.save(update_fields=['push_sent', 'push_sent_at'])
        logger.info(f'Push notification sent for alert {alert_event.id} to {total_success} devices')
        return True
    
    return False


def send_multi_user_push(users, title, body, data=None):
    """
    Send a push notification to multiple users.
    
    Args:
        users: Queryset or list of User instances
        title: Notification title
        body: Notification body/message
        data: Optional dict of custom data
    
    Returns:
        tuple: (total_success, total_failure)
    """
    total_success = 0
    total_failure = 0
    
    for user in users:
        success, failure = send_push_notification(user, title, body, data)
        total_success += success
        total_failure += failure
    
    return (total_success, total_failure)
