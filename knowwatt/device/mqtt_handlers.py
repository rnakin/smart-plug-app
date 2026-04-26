"""
MQTT message handlers for device events.
"""
import json
import logging
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from device.models import ElectricalDevice, NFCTag, PlugSession,SmartPlug

logger = logging.getLogger(__name__)
from django.db import close_old_connections

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


def handle_nfc_event(client, topic, payload_dict):
    try:
        close_old_connections()

        plug_id = payload_dict.get('plug_id')
        uid = payload_dict.get('uid')

        if not plug_id:
            logger.warning("handle_nfc_event: missing plug_id")
            return

        plug = SmartPlug.objects.select_related('house').filter(plug_code=plug_id).first()
        if not plug:
            logger.warning(f"handle_nfc_event: no plug found for {plug_id}")
            return

        house_id = str(plug.house.id)
        channel_layer = get_channel_layer()

        # ── device removed ──────────────────────────────────────
        if not uid or uid == 'null':
            PlugSession.objects.filter(plug=plug, is_active=True).update(
                is_active=False,
                ended_at=now()
            )
            logger.info(f"NFC null: device removed from plug {plug_id}")
            async_to_sync(channel_layer.group_send)(
                f"house_{house_id}",
                {
                    "type": "house.event",
                    "event": "device_removed",
                    "plug_code": plug_id,
                    "plug_id": str(plug.id),
                }
            )
            return

        # ── nfc scan ────────────────────────────────────────────
        try:
            nfc_tag = NFCTag.objects.select_related('device').get(tag_uid=uid)
        except NFCTag.DoesNotExist:
            nfc_tag = None

        if nfc_tag and nfc_tag.device:
            PlugSession.objects.filter(plug=plug, is_active=True).update(
                is_active=False,
                ended_at=now()
            )
            PlugSession.objects.create(
                plug=plug,
                device=nfc_tag.device,
                nfc_tag=nfc_tag,
            )
            logger.info(f"NFC known: {uid} → {nfc_tag.device.name} on plug {plug_id}")
            async_to_sync(channel_layer.group_send)(
                f"house_{house_id}",
                {
                    "type": "house.event",
                    "event": "nfc_known",
                    "plug_code": plug_id,
                    "plug_id": str(plug.id),
                    "device_name": nfc_tag.device.name,
                }
            )
        else:
            logger.info(f"NFC unknown: {uid} on plug {plug_id}")
            async_to_sync(channel_layer.group_send)(
                f"house_{house_id}",
                {
                    "type": "house.event",
                    "event": "nfc_unknown",
                    "plug_code": plug_id,
                    "plug_id": str(plug.id),
                    "plug_name": plug.name,
                    "uid": uid,
                }
            )

    except Exception as e:
        logger.error(f"handle_nfc_event error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        close_old_connections()

