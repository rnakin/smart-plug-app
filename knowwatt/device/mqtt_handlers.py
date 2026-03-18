"""
MQTT message handlers for device events.
"""
import json
import logging
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


def send_plug_update(plug_code, event, uid, known, device_name=None, device_type=None, risk_level=None, rated_watts=None):
    """
    Send a plug status update to all connected WebSocket clients.
    """
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'plug_{plug_code}',
            {
                'type': 'plug.update',
                'event': event,
                'uid': uid,
                'known': known,
                'device_name': device_name,
                'device_type': device_type,
                'risk_level': risk_level,
                'rated_watts': rated_watts,
                'timestamp': str(timezone.now()),
            }
        )
        logger.info(f'Sent WebSocket update to plug_{plug_code}: {event}')
    except Exception as e:
        logger.error(f'Failed to send WebSocket update: {e}')


def handle_nfc_event(client, topic, payload_bytes):
    """
    Handle incoming NFC scan events from smart plugs.
    
    Args:
        client: MQTT client instance for publishing responses
        topic: MQTT topic (format: {plug_code}/event)
        payload_bytes: Raw payload bytes from MQTT message
    """
    # Import here to avoid circular imports
    from device.models import SmartPlug, NFCTag, PlugSession, ElectricalDevice
    
    try:
        # Step 1: Parse plug_code from topic (first segment before "/")
        topic_parts = topic.split('/')
        if len(topic_parts) < 2:
            logger.warning(f'Invalid topic format: {topic}')
            return
        
        plug_code = topic_parts[0]
        logger.info(f'Processing NFC event for plug: {plug_code}')
        
        # Step 2: Parse JSON from payload_bytes
        try:
            payload = json.loads(payload_bytes.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse JSON payload: {e}')
            return
        except UnicodeDecodeError as e:
            logger.error(f'Failed to decode payload: {e}')
            return
        
        # Step 3: If type != "nfc_scan" → return silently
        event_type = payload.get('type')
        if event_type != 'nfc_scan':
            logger.debug(f'Ignoring non-NFC event type: {event_type}')
            return
        
        # Step 4: Look up SmartPlug by plug_code
        try:
            plug = SmartPlug.objects.get(plug_code=plug_code)
        except SmartPlug.DoesNotExist:
            logger.warning(f'SmartPlug not found for plug_code: {plug_code}')
            return
        
        detected = payload.get('detected', False)
        uid = payload.get('uid')
        
        # Step 5: If detected == False
        if not detected:
            logger.info(f'No tag detected on plug {plug_code}')
            
            # Close active PlugSession for this plug if one exists
            now = timezone.now()
            active_sessions = PlugSession.objects.filter(plug=plug, is_active=True)
            if active_sessions.exists():
                active_sessions.update(is_active=False, ended_at=now)
                logger.info(f'Closed active session for plug {plug_code}')
            
            # Send WebSocket update for tag removal
            send_plug_update(plug_code, 'nfc_removed', uid=None, known=False)
            
            return
        
        # Step 6: If detected == True, uid is present
        if detected and uid:
            now = timezone.now()
            
            # Look up NFCTag by tag_uid=uid — use get_or_create to avoid race conditions
            tag, created = NFCTag.objects.get_or_create(
                tag_uid=uid,
                defaults={'device': None, 'label': ''}
            )
            if created:
                logger.info(f'Created new NFCTag for uid: {uid}')
            
            # Check if tag has a registered device
            if tag.device is not None:
                # FOUND and tag.device is not None (registered tag)
                logger.info(f'Known device: {tag.device.name}')
                
                # Update SmartPlug: is_on=True, online_status="online"
                plug.is_on = True
                plug.online_status = 'online'
                plug.save()
                
                # Close any existing active PlugSession for this plug
                active_sessions = PlugSession.objects.filter(plug=plug, is_active=True)
                if active_sessions.exists():
                    active_sessions.update(is_active=False, ended_at=now)
                
                # Create new PlugSession
                PlugSession.objects.create(
                    plug=plug,
                    device=tag.device,
                    nfc_tag=tag,
                    is_active=True,
                    started_at=now
                )
                logger.info(f'Created new session for known device: {tag.device.name}')
                
                # Publish to {plug_code}/config
                config_payload = {
                    'uid': tag.tag_uid,
                    'device_name': tag.device.name,
                    'device_type': tag.device.device_type,
                    'risk_level': tag.device.risk_level,
                    'rated_watts': tag.device.rated_power_watts
                }
                
                publish_topic = f'{plug_code}/config'
                client.publish(publish_topic, json.dumps(config_payload))
                logger.info(f'Published config to {publish_topic}')
                
                # Send WebSocket update for known device
                send_plug_update(
                    plug_code,
                    'nfc_scan',
                    uid=tag.tag_uid,
                    known=True,
                    device_name=tag.device.name,
                    device_type=tag.device.device_type,
                    risk_level=tag.device.risk_level,
                    rated_watts=tag.device.rated_power_watts
                )
                
            else:
                # tag.device is None (unknown/unregistered tag)
                logger.info(f'Unknown tag: {uid} — waiting for user registration')
                
                # Check if an active session already exists for this plug with this tag
                existing_session = PlugSession.objects.filter(
                    plug=plug, nfc_tag=tag, is_active=True
                ).first()
                
                if existing_session:
                    # Tag is still present — do not create a duplicate session
                    logger.info(f'Tag {uid} still present on plug {plug_code}, session already active — skipping')
                    return
                
                # Close any other active PlugSession for this plug (different tag)
                active_sessions = PlugSession.objects.filter(plug=plug, is_active=True)
                if active_sessions.exists():
                    active_sessions.update(is_active=False, ended_at=now)
                
                # Create PlugSession with device=None
                PlugSession.objects.create(
                    plug=plug,
                    device=None,
                    nfc_tag=tag,
                    is_active=True,
                    started_at=now
                )
                logger.info(f'Created session for unregistered tag: {uid}')
                
                # Do NOT publish back to MQTT — wait for user to register this tag
                # But DO send WebSocket update so frontend shows "unknown tag"
                send_plug_update(plug_code, 'nfc_scan', uid=uid, known=False)
    
    except Exception as e:
        logger.exception(f'Error handling NFC event: {e}')
        # Don't re-raise - let the subscriber handle connection cleanup
