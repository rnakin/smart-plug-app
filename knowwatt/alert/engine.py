"""
Shared helpers used by the escalation engine and the session respond view.

  execute_auto_off(plug)             — turn off relay via MQTT + update DB
  end_session(session)               — mark PlugSession inactive
  broadcast_session_ended(...)       — WebSocket broadcast to house group
"""

import json
import logging
import ssl
from django.utils.timezone import now

logger = logging.getLogger(__name__)


def execute_auto_off(plug):
    """Turn off the relay via MQTT and mark the plug as off in the DB."""
    import paho.mqtt.publish as mqtt_publish
    from django.conf import settings

    print(f"[AUTO_OFF] Turning off plug {plug.plug_code} (id={plug.id})")
    plug.is_on = False
    plug.relay_state = False
    plug.save(update_fields=['is_on', 'relay_state'])
    print(f"[AUTO_OFF] DB updated for plug {plug.plug_code}")

    try:
        auth = None
        if getattr(settings, 'MQTT_USER', None) and getattr(settings, 'MQTT_PASSWORD', None):
            auth = {'username': settings.MQTT_USER, 'password': settings.MQTT_PASSWORD}

        topic = f"{plug.plug_code}/command"
        payload = json.dumps({"command": "turn_off"})
        print(f"[AUTO_OFF] Publishing MQTT: topic={topic} payload={payload}")

        mqtt_publish.single(
            topic,
            payload=payload,
            hostname=settings.MQTT_BROKER,
            port=settings.MQTT_PORT,
            auth=auth,
            qos=1,
            retain=False,
            tls={'tls_version': ssl.PROTOCOL_TLS_CLIENT} if getattr(settings, 'MQTT_USE_TLS', True) else None,
        )
        print(f"[AUTO_OFF] MQTT sent successfully to {plug.plug_code}")
        logger.info(f"Auto-off MQTT sent to {plug.plug_code}")
    except Exception as e:
        print(f"[AUTO_OFF] MQTT FAILED for {plug.plug_code}: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"execute_auto_off MQTT failed for {plug.plug_code}: {e}")


def end_session(session):
    """Mark a PlugSession as ended right now."""
    print(f"[AUTO_OFF] Ending session {session.id}")
    session.is_active = False
    session.ended_at = now()
    session.save(update_fields=['is_active', 'ended_at'])
    print(f"[AUTO_OFF] Session {session.id} ended successfully")
    logger.info(f"Session {session.id} ended")


def broadcast_session_ended(
    house_id, session_id, plug_id, plug_name, device_name='', reason='user_cutoff'
):
    """
    Send a session_ended event to the house WebSocket group.

    reason values:
        'user_cutoff'  — user clicked "No, turn off"
        'auto_cutoff'  — timer expired, system cut off automatically
        'nfc_removed'  — NFC tag removed from plug
    """
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    print(f"[AUTO_OFF] Broadcasting session_ended for session {session_id}")
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"house_{house_id}",
            {
                "type": "house.event",
                "event": "session_ended",
                "session_id": str(session_id),
                "plug_id": str(plug_id),
                "plug_name": plug_name,
                "device_name": device_name,
                "reason": reason,
                "house_id": str(house_id),
            },
        )
        print(f"[AUTO_OFF] Broadcast session_ended succeeded")
        logger.info(f"Broadcast session_ended ({reason}) for session {session_id}")
    except Exception as e:
        print(f"[AUTO_OFF] Broadcast session_ended FAILED: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"Broadcast session_ended failed: {e}")
