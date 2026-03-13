from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SmartPlug, ElectricalDevice, NFCTag, PlugSession
from house.models import House, HouseMember
from energy.models import EnergyReading


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


DEVICE_TYPE_EMOJI = {
    'kitchen': '🍳', 'appliance': '🔌', 'entertainment': '📺',
    'lighting': '💡', 'hvac': '❄️', 'office': '💻', 'other': '🔌',
}

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
        'device_type': device.device_type if device else None,
        'device_emoji': DEVICE_TYPE_EMOJI.get(device.device_type, '🔌') if device else None,
        'device_risk': device.risk_level if device else None,
    }


def device_to_dict(dev):
    return {
        'id': str(dev.id),
        'house_id': str(dev.house_id),
        'name': dev.name,
        'device_type': dev.device_type,
        'rated_power_watts': dev.rated_power_watts,
        'risk_level': dev.risk_level,
        'auto_cutoff_minutes': dev.auto_cutoff_minutes,
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
        device_type = request.data.get('device_type', 'other')
        rated_power = request.data.get('rated_power_watts')
        risk_level = request.data.get('risk_level', 'low')
        auto_cutoff = request.data.get('auto_cutoff_minutes')

        if not name:
            return Response({'error': 'name is required'}, status=400)
        if rated_power is None:
            return Response({'error': 'rated_power_watts is required'}, status=400)
        if device_type not in [c[0] for c in ElectricalDevice.DEVICE_TYPE_CHOICES]:
            return Response({'error': 'Invalid device_type'}, status=400)
        if risk_level not in ('low', 'medium', 'high'):
            return Response({'error': 'risk_level must be low, medium, or high'}, status=400)

        device = ElectricalDevice.objects.create(
            house_id=house_id,
            name=name,
            device_type=device_type,
            rated_power_watts=float(rated_power),
            risk_level=risk_level,
            auto_cutoff_minutes=int(auto_cutoff) if auto_cutoff is not None else None,
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

        for field in ('name', 'device_type', 'risk_level'):
            if field in request.data:
                setattr(device, field, request.data[field])
        if 'rated_power_watts' in request.data:
            device.rated_power_watts = float(request.data['rated_power_watts'])
        if 'auto_cutoff_minutes' in request.data:
            val = request.data['auto_cutoff_minutes']
            device.auto_cutoff_minutes = int(val) if val is not None else None

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
