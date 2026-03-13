from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import AlertRule, AlertEvent, UserPushToken
from device.models import SmartPlug, ElectricalDevice
from house.models import HouseMember


# ── helpers ──────────────────────────────────────────────────────────────────

def require_membership(house_id, user, min_role=None):
    m = HouseMember.objects.filter(house_id=house_id, user=user).first()
    if not m:
        return None, Response({'error': 'You are not a member of this house'}, status=403)
    if min_role == 'admin' and m.role not in ('owner', 'admin'):
        return None, Response({'error': 'Only owner or admin can perform this action'}, status=403)
    return m, None


def rule_to_dict(rule):
    return {
        'id': str(rule.id),
        'house_id': str(rule.house_id),
        'plug_id': str(rule.plug_id) if rule.plug_id else None,
        'plug_name': rule.plug.name if rule.plug else None,
        'device_id': str(rule.device_id) if rule.device_id else None,
        'device_name': rule.device.name if rule.device else None,
        'trigger': rule.trigger,
        'threshold_value': rule.threshold_value,
        'action': rule.action,
        'is_active': rule.is_active,
        'created_at': rule.created_at.isoformat(),
    }


def event_to_dict(event):
    return {
        'id': str(event.id),
        'house_id': str(event.house_id),
        'rule_id': str(event.rule_id),
        'plug_id': str(event.plug_id) if event.plug_id else None,
        'plug_name': event.plug.name if event.plug else None,
        'device_id': str(event.device_id) if event.device_id else None,
        'device_name': event.device.name if event.device else None,
        'title': event.title,
        'message': event.message,
        'trigger_value': event.trigger_value,
        'status': event.status,
        'triggered_at': event.triggered_at.isoformat(),
        'resolved_at': event.resolved_at.isoformat() if event.resolved_at else None,
        'snooze_until': event.snooze_until.isoformat() if event.snooze_until else None,
        'push_sent': event.push_sent,
    }


# ── Alert Rule endpoints ──────────────────────────────────────────────────────

class AlertRuleListCreateView(APIView):
    """
    GET  /api/houses/<house_id>/alerts/rules/   - list rules
    POST /api/houses/<house_id>/alerts/rules/   - create rule
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, house_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err
        rules = AlertRule.objects.filter(house_id=house_id).select_related('plug', 'device')
        return Response([rule_to_dict(r) for r in rules])

    def post(self, request, house_id):
        membership, err = require_membership(house_id, request.user, min_role='admin')
        if err:
            return err

        trigger = request.data.get('trigger')
        action = request.data.get('action', 'notify')
        threshold = request.data.get('threshold_value')
        plug_id = request.data.get('plug_id')
        device_id = request.data.get('device_id')

        valid_triggers = [c[0] for c in AlertRule.TRIGGER_CHOICES]
        if trigger not in valid_triggers:
            return Response({'error': f'trigger must be one of: {valid_triggers}'}, status=400)

        if action not in ('notify', 'auto_off'):
            return Response({'error': 'action must be notify or auto_off'}, status=400)

        # Validate plug/device belong to house
        plug = None
        if plug_id:
            try:
                plug = SmartPlug.objects.get(id=plug_id, house_id=house_id)
            except SmartPlug.DoesNotExist:
                return Response({'error': 'Plug not found in this house'}, status=404)

        device = None
        if device_id:
            try:
                device = ElectricalDevice.objects.get(id=device_id, house_id=house_id)
            except ElectricalDevice.DoesNotExist:
                return Response({'error': 'Device not found in this house'}, status=404)

        rule = AlertRule.objects.create(
            house_id=house_id,
            plug=plug,
            device=device,
            trigger=trigger,
            threshold_value=float(threshold) if threshold is not None else None,
            action=action,
            created_by=request.user,
        )
        return Response(rule_to_dict(rule), status=201)


class AlertRuleDetailView(APIView):
    """
    GET    /api/houses/<house_id>/alerts/rules/<rule_id>/
    PATCH  /api/houses/<house_id>/alerts/rules/<rule_id>/
    DELETE /api/houses/<house_id>/alerts/rules/<rule_id>/
    """
    permission_classes = [IsAuthenticated]

    def _get_rule(self, house_id, rule_id):
        try:
            return AlertRule.objects.select_related('plug', 'device').get(
                id=rule_id, house_id=house_id
            )
        except AlertRule.DoesNotExist:
            return None

    def get(self, request, house_id, rule_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err
        rule = self._get_rule(house_id, rule_id)
        if not rule:
            return Response({'error': 'Rule not found'}, status=404)
        return Response(rule_to_dict(rule))

    def patch(self, request, house_id, rule_id):
        membership, err = require_membership(house_id, request.user, min_role='admin')
        if err:
            return err
        rule = self._get_rule(house_id, rule_id)
        if not rule:
            return Response({'error': 'Rule not found'}, status=404)

        for field in ('trigger', 'action'):
            if field in request.data:
                setattr(rule, field, request.data[field])
        if 'threshold_value' in request.data:
            v = request.data['threshold_value']
            rule.threshold_value = float(v) if v is not None else None
        if 'is_active' in request.data:
            rule.is_active = bool(request.data['is_active'])
        rule.save()
        return Response(rule_to_dict(rule))

    def delete(self, request, house_id, rule_id):
        membership, err = require_membership(house_id, request.user, min_role='admin')
        if err:
            return err
        rule = self._get_rule(house_id, rule_id)
        if not rule:
            return Response({'error': 'Rule not found'}, status=404)
        rule.delete()
        return Response({'message': 'Rule deleted'})


# ── Alert Event endpoints ─────────────────────────────────────────────────────

class AlertEventListView(APIView):
    """
    GET /api/houses/<house_id>/alerts/events/
    Query params: status (pending|acknowledged|snoozed|dismissed|auto_resolved), limit, offset
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, house_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err

        qs = AlertEvent.objects.filter(house_id=house_id).select_related('plug', 'device')
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        limit = min(int(request.query_params.get('limit', 50)), 200)
        offset = int(request.query_params.get('offset', 0))
        total = qs.count()

        return Response({
            'total': total,
            'limit': limit,
            'offset': offset,
            'results': [event_to_dict(e) for e in qs[offset:offset + limit]],
        })


class AlertEventActionView(APIView):
    """
    POST /api/houses/<house_id>/alerts/events/<event_id>/action/
    Body: { "action": "acknowledge" | "snooze" | "dismiss" | "auto_off" }
    For snooze: { "action": "snooze", "snooze_minutes": 30 }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, house_id, event_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err

        try:
            event = AlertEvent.objects.select_related('plug', 'device').get(
                id=event_id, house_id=house_id
            )
        except AlertEvent.DoesNotExist:
            return Response({'error': 'Alert event not found'}, status=404)

        action = request.data.get('action')

        if action == 'acknowledge':
            event.status = 'acknowledged'
            event.resolved_at = timezone.now()
            event.save()
            return Response({'message': 'Alert acknowledged', 'event': event_to_dict(event)})

        elif action == 'snooze':
            minutes = int(request.data.get('snooze_minutes', 30))
            event.status = 'snoozed'
            event.snooze_until = timezone.now() + timedelta(minutes=minutes)
            event.save()
            return Response({'message': f'Alert snoozed for {minutes} minutes', 'event': event_to_dict(event)})

        elif action == 'dismiss':
            event.status = 'dismissed'
            event.resolved_at = timezone.now()
            event.save()
            return Response({'message': 'Alert dismissed', 'event': event_to_dict(event)})

        elif action == 'auto_off':
            # Turn off the plug immediately
            if event.plug:
                event.plug.is_on = False
                event.plug.save()
            event.status = 'acknowledged'
            event.resolved_at = timezone.now()
            event.save()
            return Response({
                'message': 'Plug turned off and alert acknowledged',
                'event': event_to_dict(event),
            })

        else:
            return Response(
                {'error': 'action must be acknowledge, snooze, dismiss, or auto_off'},
                status=400
            )


# ── Alert Trigger (called after energy ingest) ────────────────────────────────

class AlertTriggerView(APIView):
    """
    POST /api/houses/<house_id>/alerts/trigger/
    Called internally after an energy reading is ingested.
    Checks all active rules for the house and creates AlertEvents if triggered.
    Body: { "plug_id": "...", "power_w": 1200, "session_minutes": 45 }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, house_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err

        plug_id = request.data.get('plug_id')
        power_w = request.data.get('power_w', 0)
        session_minutes = request.data.get('session_minutes', 0)

        try:
            plug = SmartPlug.objects.get(id=plug_id, house_id=house_id)
        except SmartPlug.DoesNotExist:
            return Response({'error': 'Plug not found'}, status=404)

        active_session = plug.sessions.filter(is_active=True).select_related('device').first()
        current_device = active_session.device if active_session else None

        # Get active rules for this house/plug/device
        rules = AlertRule.objects.filter(
            house_id=house_id,
            is_active=True,
        ).filter(
            # Match rules scoped to this plug or house-wide
            plug__isnull=True
        ) | AlertRule.objects.filter(
            house_id=house_id,
            is_active=True,
            plug=plug,
        )

        triggered = []
        for rule in rules:
            # Skip if rule is device-specific and device doesn't match
            if rule.device and rule.device != current_device:
                continue

            fired = False
            trigger_value = None

            if rule.trigger == 'power_above' and rule.threshold_value is not None:
                if float(power_w) > rule.threshold_value:
                    fired = True
                    trigger_value = float(power_w)

            elif rule.trigger == 'power_below' and rule.threshold_value is not None:
                if float(power_w) < rule.threshold_value and plug.is_on:
                    fired = True
                    trigger_value = float(power_w)

            elif rule.trigger == 'duration_above' and rule.threshold_value is not None:
                if float(session_minutes) > rule.threshold_value:
                    fired = True
                    trigger_value = float(session_minutes)

            if not fired:
                continue

            # Avoid duplicate pending events for same rule+plug
            existing = AlertEvent.objects.filter(
                rule=rule, plug=plug, status='pending'
            ).exists()
            if existing:
                continue

            device_label = current_device.name if current_device else plug.name
            title_map = {
                'power_above': f'⚡ {device_label} ใช้ไฟเกินกำหนด',
                'power_below': f'⚠️ {device_label} ใช้ไฟต่ำผิดปกติ',
                'duration_above': f'⏰ {device_label} เปิดทิ้งไว้นานเกินไป',
            }
            msg_map = {
                'power_above': f'{device_label} ใช้พลังงาน {trigger_value:.0f}W เกินกว่า {rule.threshold_value:.0f}W ที่กำหนด',
                'power_below': f'{device_label} ใช้พลังงานเพียง {trigger_value:.0f}W ต่ำกว่า {rule.threshold_value:.0f}W',
                'duration_above': f'{device_label} เปิดทิ้งไว้ {trigger_value:.0f} นาที เกินกว่า {rule.threshold_value:.0f} นาทีที่กำหนด',
            }

            event = AlertEvent.objects.create(
                rule=rule,
                house_id=house_id,
                plug=plug,
                device=current_device,
                title=title_map.get(rule.trigger, f'Alert: {rule.trigger}'),
                message=msg_map.get(rule.trigger, f'Trigger value: {trigger_value}'),
                trigger_value=trigger_value,
            )

            # Auto-off action
            if rule.action == 'auto_off':
                plug.is_on = False
                plug.save()
                event.status = 'auto_resolved'
                event.resolved_at = timezone.now()
                event.save()

            triggered.append(event_to_dict(event))

        return Response({
            'triggered_count': len(triggered),
            'events': triggered,
        })


# ── Push Token endpoints ──────────────────────────────────────────────────────

class PushTokenView(APIView):
    """
    POST /api/alerts/push-token/   - register or update push token
    DELETE /api/alerts/push-token/ - remove push token
    Body: { "token": "...", "platform": "fcm|apns", "device_label": "..." }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get('token', '').strip()
        platform = request.data.get('platform', 'fcm')
        device_label = request.data.get('device_label', '')

        if not token:
            return Response({'error': 'token is required'}, status=400)
        if platform not in ('fcm', 'apns'):
            return Response({'error': 'platform must be fcm or apns'}, status=400)

        obj, created = UserPushToken.objects.update_or_create(
            token=token,
            defaults={
                'user': request.user,
                'platform': platform,
                'device_label': device_label,
                'is_active': True,
            }
        )
        return Response({
            'id': str(obj.id),
            'token': obj.token[:20] + '…',
            'platform': obj.platform,
            'device_label': obj.device_label,
            'registered_at': obj.registered_at.isoformat(),
        }, status=201 if created else 200)

    def delete(self, request):
        token = request.data.get('token', '').strip()
        if not token:
            return Response({'error': 'token is required'}, status=400)
        deleted, _ = UserPushToken.objects.filter(
            token=token, user=request.user
        ).delete()
        if deleted:
            return Response({'message': 'Push token removed'})
        return Response({'error': 'Token not found'}, status=404)


class UserNotificationsView(APIView):
    """
    GET /api/alerts/notifications/
    Returns all pending alert events across all houses the user is a member of.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get all house IDs the user is a member of
        house_ids = HouseMember.objects.filter(
            user=request.user
        ).values_list('house_id', flat=True)

        status_filter = request.query_params.get('status', 'pending')
        limit = min(int(request.query_params.get('limit', 50)), 200)
        offset = int(request.query_params.get('offset', 0))

        qs = AlertEvent.objects.filter(
            house_id__in=house_ids,
        ).select_related('plug', 'device', 'house')

        if status_filter != 'all':
            qs = qs.filter(status=status_filter)

        total = qs.count()

        return Response({
            'total': total,
            'limit': limit,
            'offset': offset,
            'results': [{
                **event_to_dict(e),
                'house_name': e.house.house_name,
            } for e in qs[offset:offset + limit]],
        })
