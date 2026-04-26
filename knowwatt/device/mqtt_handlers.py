"""
MQTT message handlers for device events.
"""
import json
import logging
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


def send_plug_update(plug_code, event, uid, known, device_name=None, rated_watts=None, device_id=None):
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
                'plug_code': plug_code,
                'uid': uid,
                'known': known,
                'device_id': device_id,
                'device_name': device_name,
                'rated_watts': rated_watts,
                'timestamp': str(timezone.now()),
            }
        )
        logger.info(f'Sent WebSocket update to plug_{plug_code}: {event}')
    except Exception as e:
        logger.error(f'Failed to send WebSocket update: {e}')


def handle_nfc_event(client, topic, payload_bytes=None, payload_dict=None):
    """
    Handle incoming NFC scan events from smart plugs.
    
    Args:
        client: MQTT client instance for publishing responses (optional if called from management command)
        topic: MQTT topic (format: {plug_code}/event)
        payload_bytes: Raw payload bytes from MQTT message (optional)
        payload_dict: Pre-parsed payload dictionary (optional)
    """
    # Import here to avoid circular imports
    from device.models import SmartPlug, NFCTag, PlugSession, ElectricalDevice
    
    try:
        # Step 1: Parse plug_code from topic
        if '/' in topic:
            topic_parts = topic.split('/')
            plug_code = topic_parts[0]
        else:
            # Fallback if topic is just the plug_id (from management command)
            plug_code = topic

        logger.info(f'Processing NFC event for plug: {plug_code}')
        
        # Step 2: Parse JSON from payload_bytes or use payload_dict
        if payload_dict:
            payload = payload_dict
        else:
            try:
                payload = json.loads(payload_bytes.decode('utf-8'))
            except Exception as e:
                logger.error(f'Failed to parse payload: {e}')
                return
        
        # Step 4: Validate payload structure
        if not isinstance(payload, dict):
            logger.error(f'Invalid payload format')
            return
        
        # Step 4: If type != "nfc_scan" → return silently
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
        
        uid = payload.get('uid')
        if uid == "null" or not uid:
            detected = False
        else:
            detected = True
        
        # Step 5: If detected == False
        if not detected:
            logger.info(f'No tag detected on plug {plug_code}')
            
            # Close active PlugSession for this plug if one exists
            now = timezone.now()
            active_sessions = PlugSession.objects.filter(plug=plug, is_active=True)
            if active_sessions.exists():
                active_sessions.update(is_active=False, ended_at=now)
                logger.info(f'Closed active session for plug {plug_code}')
            
            plug.active_uid = None
            # Do NOT turn off the plug automatically if tag is removed, 
            # as per general smart home behavior unless specified.
            # But requirement says "update that plug Electrical device to the device associated"
            # which implies the association is active when tag is present.
            plug.save()

            # Send WebSocket update for tag removal
            send_plug_update(plug_code, 'nfc_removed', uid=None, known=False)
            
            return
        
        # Step 6: If detected == True, uid is present
        if detected and uid:
            now = timezone.now()
            
            # Look up NFCTag by tag_uid=uid
            tag, created = NFCTag.objects.get_or_create(
                tag_uid=uid,
                defaults={'device': None, 'label': ''}
            )
            
            plug.active_uid = uid
            
            # Check if tag has a registered device
            if tag.device is not None:
                logger.info(f'Known device: {tag.device.name}')
                
                # Close any existing active PlugSession for this plug
                PlugSession.objects.filter(plug=plug, is_active=True).update(is_active=False, ended_at=now)
                
                # Create new PlugSession
                PlugSession.objects.create(
                    plug=plug,
                    device=tag.device,
                    nfc_tag=tag,
                    is_active=True,
                    started_at=now
                )
                
                plug.save()

                # Publish to {plug_code}/config if client is available
                if client:
                    config_payload = {
                        'uid': tag.tag_uid,
                        'device_name': tag.device.name,
                        'rated_watts': tag.device.rated_power_watts
                    }
                    publish_topic = f'{plug_code}/config'
                    client.publish(publish_topic, json.dumps(config_payload))
                
                # Send WebSocket update for known device
                send_plug_update(
                    plug_code,
                    'nfc_scan',
                    uid=tag.tag_uid,
                    known=True,
                    device_id=str(tag.device.id),
                    device_name=tag.device.name,
                    rated_watts=tag.device.rated_power_watts
                )
                
            else:
                # tag.device is None (unknown/unregistered tag)
                logger.info(f'Unknown tag: {uid}')
                
                # Close any other active PlugSession for this plug
                PlugSession.objects.filter(plug=plug, is_active=True).update(is_active=False, ended_at=now)
                
                # Create PlugSession with device=None
                PlugSession.objects.create(
                    plug=plug,
                    device=None,
                    nfc_tag=tag,
                    is_active=True,
                    started_at=now
                )
                
                plug.save()
                
                # Send WebSocket update so frontend shows popup
                send_plug_update(plug_code, 'nfc_scan', uid=uid, known=False)
    
    except Exception as e:
        logger.exception(f'Error handling NFC event: {e}')

    
    except Exception as e:
        logger.exception(f'Error handling NFC event: {e}')
        # Don't re-raise - let the subscriber handle connection cleanup

