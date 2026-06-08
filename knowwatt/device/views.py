import json
import logging
import threading
import ssl
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SmartPlug, ElectricalDevice, NFCTag, PlugSession
from house.models import House, HouseMember
from energy.models import EnergyReading

from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


def _mqtt_relay_async(plug_code, action):
    """Fire-and-forget MQTT relay control in a background thread."""
    def _send():
        import paho.mqtt.publish as mqtt_publish
        from django.conf import settings
        command = "turn_on" if action == "on" else "turn_off"
        try:
            auth = None
            if getattr(settings, 'MQTT_USER', None) and getattr(settings, 'MQTT_PASSWORD', None):
                auth = {'username': settings.MQTT_USER, 'password': settings.MQTT_PASSWORD}
            mqtt_publish.single(
                f"{plug_code}/command",
                payload=json.dumps({"command": command}),
                hostname=settings.MQTT_BROKER,
                port=settings.MQTT_PORT,
                auth=auth,
                qos=1,
                tls={'tls_version': ssl.PROTOCOL_TLS_CLIENT} if getattr(settings, 'MQTT_USE_TLS', True) else None,
            )
        except Exception as e:
            logger.error(f"MQTT relay failed for {plug_code}: {e}")
    threading.Thread(target=_send, daemon=True).start()

# ── helpers ──────────────────────────────────────────────────────────────────

def get_membership(house_id, user):
    return HouseMember.objects.filter(house_id=house_id, user=user).first()


def require_membership(house_id, user, min_role=None):
    """
    Returns (membership, error_response).
    min_role: None = any member, 'admin' = admin or owner, 'owner' = owner only
    """
    m = get_membership(house_id, user)
    if not m:
        return None, Response({'error': 'You are not a member of this house'}, status=403)
    if min_role == 'owner' and m.role != 'owner':
        return None, Response({'error': 'Only owner can perform this action'}, status=403)
    if min_role == 'admin' and m.role not in ('owner', 'admin'):
        return None, Response({'error': 'Only owner or admin can perform this action'}, status=403)
    return m, None


def plug_to_dict(plug):
    # Active session → detected device
    active_session = plug.sessions.filter(is_active=True).select_related('device').first()
    device = active_session.device if active_session else None
    # Latest energy reading
    latest = EnergyReading.objects.filter(plug=plug).order_by('-recorded_at').first()
    return {
        'id': str(plug.id),
        'house_id': str(plug.house_id),
        'plug_code': plug.plug_code,
        'name': plug.name,
        'location': plug.location,
        'is_on': plug.is_on,
        'online_status': plug.online_status,
        'registered_at': plug.registered_at.isoformat(),
        'current_power_w': round(latest.power_w, 1) if latest else None,
        'device_id': str(device.id) if device else None,
        'device_name': device.name if device else None,
    }


def device_to_dict(dev):
    return {
        'id': str(dev.id),
        'house_id': str(dev.house_id),
        'name': dev.name,
        'rated_power_watts': dev.rated_power_watts,
        'until_notify_minutes': dev.until_notify_minutes,
        'until_alert_minutes': dev.until_alert_minutes,
        'until_cutoff_minutes': dev.until_cutoff_minutes,
        'created_at': dev.created_at.isoformat(),
    }


def nfc_to_dict(tag):
    return {
        'id': str(tag.id),
        'tag_uid': tag.tag_uid,
        'device_id': str(tag.device_id) if tag.device_id else None,
        'device_name': tag.device.name if tag.device else None,
        'label': tag.label,
        'registered_at': tag.registered_at.isoformat(),
    }


# ── Smart Plug endpoints ──────────────────────────────────────────────────────

class SmartPlugListCreateView(APIView):
    """
    GET  /api/houses/<house_id>/plugs/        - list plugs in house
    POST /api/houses/<house_id>/plugs/        - register new plug
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, house_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err
        plugs = SmartPlug.objects.filter(house_id=house_id)
        return Response([plug_to_dict(p) for p in plugs])

    def post(self, request, house_id):
        membership, err = require_membership(house_id, request.user, min_role='admin')
        if err:
            return err

        plug_code = request.data.get('plug_code', '').strip()
        name = request.data.get('name', '').strip()
        location = request.data.get('location', '').strip()

        if not plug_code:
            return Response({'error': 'plug_code is required'}, status=400)
        if not name:
            return Response({'error': 'name is required'}, status=400)

        if SmartPlug.objects.filter(plug_code=plug_code).exists():
            return Response({'error': 'A plug with this code is already registered'}, status=400)

        plug = SmartPlug.objects.create(
            house_id=house_id,
            plug_code=plug_code,
            name=name,
            location=location,
            registered_by=request.user,
        )
        return Response(plug_to_dict(plug), status=201)


class SmartPlugDetailView(APIView):
    """
    GET    /api/houses/<house_id>/plugs/<plug_id>/  - get plug details
    PATCH  /api/houses/<house_id>/plugs/<plug_id>/  - update name/location
    DELETE /api/houses/<house_id>/plugs/<plug_id>/  - remove plug
    """
    permission_classes = [IsAuthenticated]

    def _get_plug(self, house_id, plug_id):
        try:
            return SmartPlug.objects.get(id=plug_id, house_id=house_id)
        except SmartPlug.DoesNotExist:
            return None

    def get(self, request, house_id, plug_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err
        plug = self._get_plug(house_id, plug_id)
        if not plug:
            return Response({'error': 'Plug not found'}, status=404)
        return Response(plug_to_dict(plug))

    def patch(self, request, house_id, plug_id):
        membership, err = require_membership(house_id, request.user, min_role='admin')
        if err:
            return err
        plug = self._get_plug(house_id, plug_id)
        if not plug:
            return Response({'error': 'Plug not found'}, status=404)

        if 'name' in request.data:
            plug.name = request.data['name'].strip()
        if 'location' in request.data:
            plug.location = request.data['location'].strip()
        plug.save()
        return Response(plug_to_dict(plug))

    def delete(self, request, house_id, plug_id):
        membership, err = require_membership(house_id, request.user, min_role='admin')
        if err:
            return err
        plug = self._get_plug(house_id, plug_id)
        if not plug:
            return Response({'error': 'Plug not found'}, status=404)
        plug.delete()
        return Response({'message': 'Plug removed successfully'})


class SmartPlugControlView(APIView):
    """
    POST /api/houses/<house_id>/plugs/<plug_id>/control/
    Body: { "action": "on" | "off" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, house_id, plug_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err

        # Guests cannot control
        if membership.role == 'guest':
            return Response({'error': 'Guests cannot control devices'}, status=403)

        try:
            plug = SmartPlug.objects.get(id=plug_id, house_id=house_id)
        except SmartPlug.DoesNotExist:
            return Response({'error': 'Plug not found'}, status=404)

        action = request.data.get('action')
        if action == 'on':
            plug.is_on = True
        elif action == 'off':
            plug.is_on = False
        else:
            return Response({'error': 'action must be "on" or "off"'}, status=400)

        plug.save()
        _mqtt_relay_async(plug.plug_code, action)
        return Response({'id': str(plug.id), 'is_on': plug.is_on})


# ── Electrical Device endpoints ───────────────────────────────────────────────

class ElectricalDeviceListCreateView(APIView):
    """
    GET  /api/houses/<house_id>/devices/   - list devices in house
    POST /api/houses/<house_id>/devices/   - create device
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, house_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err
        devices = ElectricalDevice.objects.filter(house_id=house_id)
        return Response([device_to_dict(d) for d in devices])

    def post(self, request, house_id):
        membership, err = require_membership(house_id, request.user, min_role='admin')
        if err:
            return err

        name = request.data.get('name', '').strip()
        rated_power = request.data.get('rated_power_watts')
        until_notify = request.data.get('until_notify_minutes')
        until_alert = request.data.get('until_alert_minutes')
        until_cutoff = request.data.get('until_cutoff_minutes')

        if not name:
            return Response({'error': 'name is required'}, status=400)
        if rated_power is None:
            return Response({'error': 'rated_power_watts is required'}, status=400)

        device = ElectricalDevice.objects.create(
            house_id=house_id,
            name=name,
            rated_power_watts=float(rated_power),
            until_notify_minutes=int(until_notify) if until_notify is not None else None,
            until_alert_minutes=int(until_alert) if until_alert is not None else None,
            until_cutoff_minutes=int(until_cutoff) if until_cutoff is not None else None,
            created_by=request.user,
        )
        return Response(device_to_dict(device), status=201)


class ElectricalDeviceDetailView(APIView):
    """
    GET    /api/houses/<house_id>/devices/<device_id>/
    PATCH  /api/houses/<house_id>/devices/<device_id>/
    DELETE /api/houses/<house_id>/devices/<device_id>/
    """
    permission_classes = [IsAuthenticated]

    def _get_device(self, house_id, device_id):
        try:
            return ElectricalDevice.objects.get(id=device_id, house_id=house_id)
        except ElectricalDevice.DoesNotExist:
            return None

    def get(self, request, house_id, device_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err
        device = self._get_device(house_id, device_id)
        if not device:
            return Response({'error': 'Device not found'}, status=404)
        return Response(device_to_dict(device))

    def patch(self, request, house_id, device_id):
        membership, err = require_membership(house_id, request.user, min_role='admin')
        if err:
            return err
        device = self._get_device(house_id, device_id)
        if not device:
            return Response({'error': 'Device not found'}, status=404)

        if 'name' in request.data:
            device.name = request.data['name']
        if 'rated_power_watts' in request.data:
            device.rated_power_watts = float(request.data['rated_power_watts'])
        for field in ('until_notify_minutes', 'until_alert_minutes', 'until_cutoff_minutes'):
            if field in request.data:
                val = request.data[field]
                setattr(device, field, int(val) if val is not None else None)

        device.save()
        return Response(device_to_dict(device))

    def delete(self, request, house_id, device_id):
        membership, err = require_membership(house_id, request.user, min_role='admin')
        if err:
            return err
        device = self._get_device(house_id, device_id)
        if not device:
            return Response({'error': 'Device not found'}, status=404)
        device.delete()
        return Response({'message': 'Device deleted successfully'})


# ── NFC Tag endpoints ─────────────────────────────────────────────────────────

class NFCTagListView(APIView):
    """
    GET /api/houses/<house_id>/nfc/   - list all NFC tags for devices in this house
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, house_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err
        tags = NFCTag.objects.filter(device__house_id=house_id).select_related('device')
        return Response([nfc_to_dict(t) for t in tags])


class NFCTagRegisterView(APIView):
    """
    POST /api/houses/<house_id>/nfc/register/
    Register a new NFC tag UID and optionally pair it with a device.
    Body: { "tag_uid": "...", "device_id": "...(optional)", "label": "...(optional)" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, house_id):
        membership, err = require_membership(house_id, request.user, min_role='admin')
        if err:
            return err

        tag_uid = request.data.get('tag_uid', '').strip()
        if not tag_uid:
            return Response({'error': 'tag_uid is required'}, status=400)

        if NFCTag.objects.filter(tag_uid=tag_uid).exists():
            return Response({'error': 'This NFC tag is already registered'}, status=400)

        device = None
        device_id = request.data.get('device_id')
        if device_id:
            try:
                device = ElectricalDevice.objects.get(id=device_id, house_id=house_id)
            except ElectricalDevice.DoesNotExist:
                return Response({'error': 'Device not found in this house'}, status=404)

        tag = NFCTag.objects.create(
            tag_uid=tag_uid,
            device=device,
            label=request.data.get('label', ''),
            registered_by=request.user,
        )
        return Response(nfc_to_dict(tag), status=201)


class NFCTagDetailView(APIView):
    """
    GET    /api/houses/<house_id>/nfc/<tag_id>/   - get tag details
    PATCH  /api/houses/<house_id>/nfc/<tag_id>/   - update label or pair to device
    DELETE /api/houses/<house_id>/nfc/<tag_id>/   - remove tag
    """
    permission_classes = [IsAuthenticated]

    def _get_tag(self, house_id, tag_id):
        try:
            return NFCTag.objects.select_related('device').get(
                id=tag_id, device__house_id=house_id
            )
        except NFCTag.DoesNotExist:
            # tag might be unregistered (no device), try by id only
            try:
                return NFCTag.objects.get(id=tag_id)
            except NFCTag.DoesNotExist:
                return None

    def get(self, request, house_id, tag_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err
        tag = self._get_tag(house_id, tag_id)
        if not tag:
            return Response({'error': 'NFC tag not found'}, status=404)
        return Response(nfc_to_dict(tag))

    def patch(self, request, house_id, tag_id):
        membership, err = require_membership(house_id, request.user, min_role='admin')
        if err:
            return err
        tag = self._get_tag(house_id, tag_id)
        if not tag:
            return Response({'error': 'NFC tag not found'}, status=404)

        if 'label' in request.data:
            tag.label = request.data['label']
        if 'device_id' in request.data:
            device_id = request.data['device_id']
            if device_id is None:
                tag.device = None
            else:
                try:
                    tag.device = ElectricalDevice.objects.get(id=device_id, house_id=house_id)
                except ElectricalDevice.DoesNotExist:
                    return Response({'error': 'Device not found in this house'}, status=404)
        tag.save()
        return Response(nfc_to_dict(tag))

    def delete(self, request, house_id, tag_id):
        membership, err = require_membership(house_id, request.user, min_role='admin')
        if err:
            return err
        tag = self._get_tag(house_id, tag_id)
        if not tag:
            return Response({'error': 'NFC tag not found'}, status=404)
        tag.delete()
        return Response({'message': 'NFC tag removed successfully'})


class NFCTagScanView(APIView):
    """
    POST /api/nfc/scan/
    Called when a plug detects an NFC tap.
    Body: { "tag_uid": "...", "plug_id": "..." }
    Returns device info if known, or signals unknown tag.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tag_uid = request.data.get('tag_uid', '').strip()
        plug_id = request.data.get('plug_id', '').strip()

        if not tag_uid or not plug_id:
            return Response({'error': 'tag_uid and plug_id are required'}, status=400)

        try:
            plug = SmartPlug.objects.get(id=plug_id)
        except SmartPlug.DoesNotExist:
            return Response({'error': 'Plug not found'}, status=404)

        # Check membership
        membership, err = require_membership(plug.house_id, request.user)
        if err:
            return err

        try:
            tag = NFCTag.objects.select_related('device').get(tag_uid=tag_uid)
        except NFCTag.DoesNotExist:
            # Unknown tag — return signal to register
            return Response({
                'known': False,
                'tag_uid': tag_uid,
                'plug_id': plug_id,
                'message': 'Unknown NFC tag. Please register this tag with a device.',
            }, status=200)

        # Close any active session on this plug
        PlugSession.objects.filter(plug=plug, is_active=True).update(
            is_active=False,
            ended_at=timezone.now()
        )

        # Open new session
        session = PlugSession.objects.create(
            plug=plug,
            device=tag.device,
            nfc_tag=tag,
        )

        return Response({
            'known': True,
            'tag_uid': tag_uid,
            'device': device_to_dict(tag.device) if tag.device else None,
            'session_id': str(session.id),
        }, status=200)


class UnregisteredNFCTagsView(APIView):
    """
    GET /api/nfc/unregistered/
    Returns NFCTag objects where device is null.
    Fields: id, tag_uid, label, registered_at
    Order by: -registered_at
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all unregistered NFC tags (where device is null)
        tags = NFCTag.objects.filter(device__isnull=True).order_by('-registered_at')
        
        data = [
            {
                'id': str(tag.id),
                'tag_uid': tag.tag_uid,
                'label': tag.label or '',
                'registered_at': tag.registered_at.isoformat() if tag.registered_at else None,
            }
            for tag in tags
        ]
        
        return Response(data, status=200)


class NFCTagRegisterView(APIView):
    """
    POST /api/nfc/{tag_uid}/register/
    Registers an NFC tag to an existing ElectricalDevice.
    Body: {
        "device_id": "uuid-of-electrical-device",
        "label": "optional label"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, tag_uid):
        device_id = request.data.get('device_id')
        label = request.data.get('label', '')
        
        if not device_id:
            return Response({'error': 'device_id is required'}, status=400)
        
        # Look up NFCTag by tag_uid — 404 if not found
        try:
            tag = NFCTag.objects.get(tag_uid=tag_uid)
        except NFCTag.DoesNotExist:
            return Response({'error': 'NFC tag not found'}, status=404)
        
        # Look up ElectricalDevice by id — 404 if not found
        try:
            device = ElectricalDevice.objects.get(id=device_id)
        except ElectricalDevice.DoesNotExist:
            return Response({'error': 'Electrical device not found'}, status=404)
        
        # Check membership - user must be member of the device's house
        membership, err = require_membership(device.house_id, request.user)
        if err:
            return err
        
        # Set tag.device = device, tag.label = label
        tag.device = device
        tag.label = label
        tag.save()
        
        # If there is an active PlugSession with this nfc_tag:
        # update session.device = device
        # publish device info to {plug_code}/config
        active_sessions = PlugSession.objects.filter(nfc_tag=tag, is_active=True)
        
        from device.mqtt_handlers import send_plug_update

        if active_sessions.exists():
            # Update session device
            active_sessions.update(device=device)
            
            # Get the plug from the session to publish config
            for session in active_sessions:
                plug = session.plug
                
                # Send WebSocket update
                send_plug_update(
                    plug.plug_code,
                    'nfc_scan',
                    uid=tag.tag_uid,
                    known=True,
                    device_id=str(device.id),
                    device_name=device.name,
                    rated_watts=device.rated_power_watts
                )

                # Publish to {plug_code}/config
                import paho.mqtt.client as mqtt
                import os
                import json
                
                MQTT_HOST = os.environ.get('MQTT_HOST', '')
                MQTT_PORT = int(os.environ.get('MQTT_PORT', 8883))
                MQTT_USER = os.environ.get('MQTT_USER', '')
                MQTT_PASS = os.environ.get('MQTT_PASS', '')
                MQTT_USE_TLS = os.environ.get('MQTT_USE_TLS', 'false').lower() == 'true'
                
                try:
                    mqtt_client = mqtt.Client(client_id='django_nfc_register')
                    if MQTT_USER:
                        mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
                    if MQTT_USE_TLS:
                        mqtt_client.tls_set()
                    
                    mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
                    
                    config_payload = {
                        'uid': tag.tag_uid,
                        'device_name': device.name,
                        'rated_watts': device.rated_power_watts
                    }
                    
                    publish_topic = f'{plug.plug_code}/config'
                    mqtt_client.publish(publish_topic, json.dumps(config_payload))
                    mqtt_client.disconnect()
                except Exception as e:
                    # Log but don't fail the request
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Failed to publish MQTT config: {e}')
        
        # Return updated NFCTag with device details
        return Response({
            'id': str(tag.id),
            'tag_uid': tag.tag_uid,
            'label': tag.label,
            'registered_at': tag.registered_at.isoformat() if tag.registered_at else None,
            'device': {
                'id': str(device.id),
                'name': device.name,
                'rated_power_watts': device.rated_power_watts,
            }
        }, status=200)

import json
import paho.mqtt.publish as publish
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.http import HttpResponse

@require_POST
@require_POST
def publish_command(request, plug_id):
    action = request.POST.get('action')
    print(f"publish_command called: plug={plug_id} action={action}")

    if action == 'on': action = 'turn_on'
    elif action == 'off': action = 'turn_off'

    if action not in ['turn_on', 'turn_off']:
        return HttpResponse("Invalid action", status=400)

    topic = f"{plug_id}/command"
    payload = json.dumps({"command": action})

    auth = None
    if settings.MQTT_USER and settings.MQTT_PASSWORD:
        auth = {'username': settings.MQTT_USER, 'password': settings.MQTT_PASSWORD}

    try:
        publish.single(
            topic,
            payload=payload,
            hostname=settings.MQTT_BROKER,
            port=settings.MQTT_PORT,
            auth=auth,
            tls={'tls_version': ssl.PROTOCOL_TLS_CLIENT} if getattr(settings, 'MQTT_USE_TLS', True) else None,
            qos=1
        )
        print(f"MQTT published: {topic} → {payload}")
        
        plug = SmartPlug.objects.filter(plug_code=plug_id).first()
        if plug:
            is_on = action == 'turn_on'
            plug.is_on = is_on
            plug.relay_state = is_on
            plug.save(update_fields=['is_on', 'relay_state'])
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'plug_{plug_id}',
                {
                    'type': 'plug.update',
                    'plug_id': str(plug.id),
                    'plug_code': plug_id,
                    'is_on': is_on,
                    'relay_state': is_on,
                    'current_power_w': plug.current_power_w,
                }
            )
            print(f"Optimistic WS broadcast: plug_{plug_id} → {action}")
    except Exception as e:
        print(f"MQTT PUBLISH FAILED: {e}")
        import traceback
        print(traceback.format_exc())

    return render(request, 'device/partials/_button_pending.html', {
        'plug_id': plug_id,
        'action': action
    })

def relay_status(request, plug_id):
    """
    Polling endpoint to check if the relay state matches the desired state.
    """
    plug = get_object_or_404(SmartPlug, plug_id=plug_id)
    target_state = request.GET.get('target')
    current_state = "turn_on" if plug.relay_state else "turn_off"
    
    if target_state and current_state != target_state:
        return render(request, 'device/partials/_button_pending.html', {
            'plug_id': plug_id,
            'action': target_state
        })

    return render(request, 'device/partials/_button_confirmed.html', {
        'plug': plug
    })

from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError

@login_required
@require_POST
def nfc_register_from_popup(request, house_id):
    """
    POST /houses/<house_id>/nfc/register/
    Called from the NFC unknown popup modal.
    Handles race condition via IntegrityError on tag_uid unique constraint.
    """
    uid = request.POST.get('uid', '').strip()
    tab = request.POST.get('tab')  # 'existing' or 'new'
    label = request.POST.get('label', '').strip()

    if not uid:
        return JsonResponse({'message': 'Missing NFC uid'}, status=400)

    # verify membership
    membership, err = require_membership(house_id, request.user)
    if err:
        return JsonResponse({'message': 'Not a member of this house'}, status=403)

    # get or create device
    if tab == 'existing':
        device_id = request.POST.get('device_id', '').strip()
        if not device_id:
            return JsonResponse({'message': 'Please select a device'}, status=400)
        try:
            device = ElectricalDevice.objects.get(id=device_id, house_id=house_id)
        except ElectricalDevice.DoesNotExist:
            return JsonResponse({'message': 'Device not found'}, status=404)

    elif tab == 'new':
        name = request.POST.get('device_name', '').strip()
        power = request.POST.get('device_power', '').strip()
        if not name or not power:
            return JsonResponse({'message': 'Device name and power are required'}, status=400)
        try:
            device = ElectricalDevice.objects.create(
                house_id=house_id,
                name=name,
                rated_power_watts=float(power),
                created_by=request.user,
            )
        except Exception as e:
            return JsonResponse({'message': f'Failed to create device: {e}'}, status=500)
    else:
        return JsonResponse({'message': 'Invalid tab'}, status=400)

    # save NFC tag — race condition handled here
    try:
        NFCTag.objects.create(
            tag_uid=uid,
            device=device,
            label=label,
            registered_by=request.user,
        )
    except IntegrityError:
        # another user already registered this tag
        return JsonResponse({'message': 'This tag was already registered by someone else'}, status=409)

    return JsonResponse({'status': 'ok', 'device_name': device.name})