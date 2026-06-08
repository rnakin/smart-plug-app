"""
MQTT message handlers for device events.
"""
import json
import logging
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from device.models import ElectricalDevice, NFCTag, PlugSession,SmartPlug
from django.utils.timezone import now
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
    print(f"handle_nfc_event called: {payload_dict}")  # add this first line
    try:
        close_old_connections()

        plug_id = payload_dict.get('plug_id')
        uid = payload_dict.get('uid')

        if not plug_id:
            print("handle_nfc_event: missing plug_id")
            return

        plug = SmartPlug.objects.select_related('house').filter(plug_code=plug_id).first()
        if not plug:
            print(f"handle_nfc_event: no plug found for {plug_id}")
            return

        house_id = str(plug.house.id)
        channel_layer = get_channel_layer()

        # ── device removed ──────────────────────────────────────
        if not uid or uid == 'null':
            # Collect active sessions before ending them so we can cancel timers
            ending_sessions = list(
                PlugSession.objects.filter(plug=plug, is_active=True).values_list('id', flat=True)
            )
            PlugSession.objects.filter(plug=plug, is_active=True).update(
                is_active=False,
                ended_at=now()
            )
            # Cancel escalation timers for every session that just ended
            from alert.escalation import cancel_escalation
            from alert.engine import broadcast_session_ended
            for sid in ending_sessions:
                cancel_escalation(str(sid))
                broadcast_session_ended(
                    house_id=house_id,
                    session_id=str(sid),
                    plug_id=str(plug.id),
                    plug_name=plug.name,
                    reason='nfc_removed',
                )
            print(f"NFC null: device removed from plug {plug_id}")
            async_to_sync(channel_layer.group_send)(
                f"house_{house_id}",
                {
                    "type": "house.event",
                    "event": "device_removed",
                    "plug_code": plug_id,
                    "plug_id": str(plug.id),
                    "online_status": "online",
                }
            )
            async_to_sync(channel_layer.group_send)(
                f"plug_{plug_id}",
                {
                    "type": "plug.update",
                    "plug_code": plug_id,
                    "plug_id": str(plug.id),
                    "online_status": "online",
                    "is_on": plug.is_on,
                    "current_device_name": None,
                    "current_power_w": plug.current_power_w,
                }
            )
            return

        # ── nfc scan ────────────────────────────────────────────
        try:
            nfc_tag = NFCTag.objects.select_related('device').get(tag_uid=uid)
        except NFCTag.DoesNotExist:
            nfc_tag = None

        if nfc_tag and nfc_tag.device:
            # Cancel timers for any session being displaced by the new scan
            ending_sessions = list(
                PlugSession.objects.filter(plug=plug, is_active=True).values_list('id', flat=True)
            )
            PlugSession.objects.filter(plug=plug, is_active=True).update(
                is_active=False,
                ended_at=now()
            )
            from alert.escalation import cancel_escalation, schedule_escalation
            from alert.engine import broadcast_session_ended
            for sid in ending_sessions:
                cancel_escalation(str(sid))
                broadcast_session_ended(
                    house_id=house_id,
                    session_id=str(sid),
                    plug_id=str(plug.id),
                    plug_name=plug.name,
                    reason='nfc_removed',
                )

            new_session = PlugSession.objects.create(
                plug=plug,
                device=nfc_tag.device,
                nfc_tag=nfc_tag,
            )
            # Arm escalation timers for the new session (only if device has limits set)
            device = nfc_tag.device
            if device.until_notify_minutes or device.until_alert_minutes or device.until_cutoff_minutes:
                schedule_escalation(str(new_session.id))

            print(f"NFC known: {uid} → {nfc_tag.device.name} on plug {plug_id}")
            async_to_sync(channel_layer.group_send)(
                f"house_{house_id}",
                {
                    "type": "house.event",
                    "event": "nfc_known",
                    "plug_code": plug_id,
                    "plug_id": str(plug.id),
                    "device_name": nfc_tag.device.name,
                    "device_id": str(nfc_tag.device.id),
                    "session_id": str(new_session.id),
                    "session_started": new_session.started_at.isoformat(),
                    "notify_min": device.until_notify_minutes,
                    "alert_min": device.until_alert_minutes,
                    "cutoff_min": device.until_cutoff_minutes,
                    "online_status": "online",
                }
            )
            async_to_sync(channel_layer.group_send)(
                f"plug_{plug_id}",
                {
                    "type": "plug.update",
                    "plug_code": plug_id,
                    "plug_id": str(plug.id),
                    "online_status": "online",
                    "is_on": plug.is_on,
                    "current_device_name": nfc_tag.device.name,
                    "current_power_w": plug.current_power_w,
                }
            )
        else:
            print(f"NFC unknown: {uid} on plug {plug_id}")
            async_to_sync(channel_layer.group_send)(
                f"house_{house_id}",
                {
                    "type": "house.event",
                    "event": "nfc_unknown",
                    "plug_code": plug_id,
                    "plug_id": str(plug.id),
                    "plug_name": plug.name,
                    "uid": uid,
                    "online_status": "online",
                }
            )
            async_to_sync(channel_layer.group_send)(
                f"plug_{plug_id}",
                {
                    "type": "plug.update",
                    "plug_code": plug_id,
                    "plug_id": str(plug.id),
                    "online_status": "online",
                    "is_on": plug.is_on,
                    "current_device_name": None,
                    "current_power_w": plug.current_power_w,
                }
            )

    except Exception as e:
        print(f"handle_nfc_event ERROR: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        close_old_connections()

