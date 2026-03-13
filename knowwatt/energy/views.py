import csv
import json
from datetime import date, timedelta, datetime

from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Avg, Max, Min, Count, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import EnergyReading, DailyEnergySummary
from device.models import SmartPlug, ElectricalDevice
from house.models import HouseMember


# ── helpers ──────────────────────────────────────────────────────────────────

def require_membership(house_id, user):
    m = HouseMember.objects.filter(house_id=house_id, user=user).first()
    if not m:
        return None, Response({'error': 'You are not a member of this house'}, status=403)
    return m, None


def parse_date_range(request, default_days=30):
    """Parse ?start=YYYY-MM-DD&end=YYYY-MM-DD from query params."""
    try:
        end = date.fromisoformat(request.query_params.get('end', date.today().isoformat()))
        start = date.fromisoformat(
            request.query_params.get('start', (end - timedelta(days=default_days)).isoformat())
        )
    except ValueError:
        end = date.today()
        start = end - timedelta(days=default_days)
    return start, end


# ── Ingest endpoint (called by plug firmware) ─────────────────────────────────

class EnergyReadingIngestView(APIView):
    """
    POST /api/houses/<house_id>/energy/ingest/
    Body: {
        "plug_id": "...",
        "voltage_v": 220.5,
        "current_a": 5.2,
        "power_w": 1144.6,
        "energy_kwh": 0.032,
        "recorded_at": "2024-01-01T12:00:00Z"   (optional, defaults to now)
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, house_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err

        plug_id = request.data.get('plug_id')
        if not plug_id:
            return Response({'error': 'plug_id is required'}, status=400)

        try:
            plug = SmartPlug.objects.get(id=plug_id, house_id=house_id)
        except SmartPlug.DoesNotExist:
            return Response({'error': 'Plug not found in this house'}, status=404)

        for field in ('voltage_v', 'current_a', 'power_w'):
            if request.data.get(field) is None:
                return Response({'error': f'{field} is required'}, status=400)

        recorded_at_raw = request.data.get('recorded_at')
        if recorded_at_raw:
            try:
                recorded_at = datetime.fromisoformat(recorded_at_raw.replace('Z', '+00:00'))
            except ValueError:
                return Response({'error': 'Invalid recorded_at format. Use ISO 8601.'}, status=400)
        else:
            recorded_at = timezone.now()

        # Get active session for device linkage
        active_session = plug.sessions.filter(is_active=True).select_related('device').first()

        reading = EnergyReading.objects.create(
            plug=plug,
            session=active_session,
            device=active_session.device if active_session else None,
            voltage_v=float(request.data['voltage_v']),
            current_a=float(request.data['current_a']),
            power_w=float(request.data['power_w']),
            energy_kwh=float(request.data.get('energy_kwh', 0)),
            recorded_at=recorded_at,
        )

        return Response({
            'id': str(reading.id),
            'plug_id': str(plug.id),
            'power_w': reading.power_w,
            'recorded_at': reading.recorded_at.isoformat(),
        }, status=201)


# ── Real-time / latest reading ────────────────────────────────────────────────

class EnergyRealtimeView(APIView):
    """
    GET /api/houses/<house_id>/energy/realtime/
    Returns the latest reading for each plug in the house.
    Optional: ?plug_id=<uuid> to filter to one plug.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, house_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err

        plug_id = request.query_params.get('plug_id')
        plugs = SmartPlug.objects.filter(house_id=house_id)
        if plug_id:
            plugs = plugs.filter(id=plug_id)

        result = []
        for plug in plugs:
            latest = EnergyReading.objects.filter(plug=plug).order_by('-recorded_at').first()
            result.append({
                'plug_id': str(plug.id),
                'plug_name': plug.name,
                'location': plug.location,
                'is_on': plug.is_on,
                'online_status': plug.online_status,
                'latest_reading': {
                    'voltage_v': latest.voltage_v,
                    'current_a': latest.current_a,
                    'power_w': latest.power_w,
                    'energy_kwh': latest.energy_kwh,
                    'recorded_at': latest.recorded_at.isoformat(),
                } if latest else None,
            })

        return Response(result)


# ── Summary endpoints ─────────────────────────────────────────────────────────

class EnergySummaryView(APIView):
    """
    GET /api/houses/<house_id>/energy/summary/
    Query params:
        period = daily | weekly | monthly  (default: daily)
        start  = YYYY-MM-DD
        end    = YYYY-MM-DD
        plug_id = <uuid>  (optional)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, house_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err

        period = request.query_params.get('period', 'daily')
        start, end = parse_date_range(request)
        plug_id = request.query_params.get('plug_id')

        qs = EnergyReading.objects.filter(
            plug__house_id=house_id,
            recorded_at__date__gte=start,
            recorded_at__date__lte=end,
        )
        if plug_id:
            qs = qs.filter(plug_id=plug_id)

        trunc_map = {
            'daily':   TruncDate,
            'weekly':  TruncWeek,
            'monthly': TruncMonth,
        }
        TruncFn = trunc_map.get(period, TruncDate)

        data = (
            qs
            .annotate(period=TruncFn('recorded_at'))
            .values('period')
            .annotate(
                total_kwh=Sum('energy_kwh'),
                avg_power_w=Avg('power_w'),
                peak_power_w=Max('power_w'),
                reading_count=Count('id'),
            )
            .order_by('period')
        )

        return Response([{
            'period': row['period'].isoformat() if row['period'] else None,
            'total_kwh': round(row['total_kwh'] or 0, 4),
            'avg_power_w': round(row['avg_power_w'] or 0, 2),
            'peak_power_w': round(row['peak_power_w'] or 0, 2),
            'reading_count': row['reading_count'],
        } for row in data])


class EnergyByDeviceView(APIView):
    """
    GET /api/houses/<house_id>/energy/by-device/
    Query params: start, end
    Returns energy breakdown per device.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, house_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err

        start, end = parse_date_range(request)

        data = (
            EnergyReading.objects
            .filter(
                plug__house_id=house_id,
                recorded_at__date__gte=start,
                recorded_at__date__lte=end,
                device__isnull=False,
            )
            .values('device__id', 'device__name', 'device__device_type')
            .annotate(
                total_kwh=Sum('energy_kwh'),
                avg_power_w=Avg('power_w'),
                peak_power_w=Max('power_w'),
                reading_count=Count('id'),
            )
            .order_by('-total_kwh')
        )

        return Response([{
            'device_id': str(row['device__id']),
            'device_name': row['device__name'],
            'device_type': row['device__device_type'],
            'total_kwh': round(row['total_kwh'] or 0, 4),
            'avg_power_w': round(row['avg_power_w'] or 0, 2),
            'peak_power_w': round(row['peak_power_w'] or 0, 2),
            'reading_count': row['reading_count'],
        } for row in data])


class EnergyByPlugView(APIView):
    """
    GET /api/houses/<house_id>/energy/by-plug/
    Query params: start, end
    Returns energy breakdown per plug.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, house_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err

        start, end = parse_date_range(request)

        data = (
            EnergyReading.objects
            .filter(
                plug__house_id=house_id,
                recorded_at__date__gte=start,
                recorded_at__date__lte=end,
            )
            .values('plug__id', 'plug__name', 'plug__location')
            .annotate(
                total_kwh=Sum('energy_kwh'),
                avg_power_w=Avg('power_w'),
                peak_power_w=Max('power_w'),
                reading_count=Count('id'),
            )
            .order_by('-total_kwh')
        )

        return Response([{
            'plug_id': str(row['plug__id']),
            'plug_name': row['plug__name'],
            'location': row['plug__location'],
            'total_kwh': round(row['total_kwh'] or 0, 4),
            'avg_power_w': round(row['avg_power_w'] or 0, 2),
            'peak_power_w': round(row['peak_power_w'] or 0, 2),
            'reading_count': row['reading_count'],
        } for row in data])


class EnergyHouseDashboardView(APIView):
    """
    GET /api/houses/<house_id>/energy/dashboard/
    Returns a combined summary for the dashboard:
    - Today's total kWh
    - This week's total kWh
    - This month's total kWh
    - Current total power (sum of latest readings)
    - Per-plug latest readings
    - Top 5 devices by energy this month
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, house_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        def kwh_sum(start_date, end_date=None):
            qs = EnergyReading.objects.filter(
                plug__house_id=house_id,
                recorded_at__date__gte=start_date,
            )
            if end_date:
                qs = qs.filter(recorded_at__date__lte=end_date)
            result = qs.aggregate(total=Sum('energy_kwh'))['total']
            return round(result or 0, 4)

        # Current power: sum of latest reading per plug
        plugs = SmartPlug.objects.filter(house_id=house_id)
        current_power_w = 0.0
        plug_status = []
        for plug in plugs:
            latest = EnergyReading.objects.filter(plug=plug).order_by('-recorded_at').first()
            pw = latest.power_w if latest else 0.0
            current_power_w += pw
            plug_status.append({
                'plug_id': str(plug.id),
                'plug_name': plug.name,
                'location': plug.location,
                'is_on': plug.is_on,
                'power_w': round(pw, 2),
                'recorded_at': latest.recorded_at.isoformat() if latest else None,
            })

        # Top 5 devices this month
        top_devices = (
            EnergyReading.objects
            .filter(
                plug__house_id=house_id,
                recorded_at__date__gte=month_start,
                device__isnull=False,
            )
            .values('device__id', 'device__name')
            .annotate(total_kwh=Sum('energy_kwh'))
            .order_by('-total_kwh')[:5]
        )

        return Response({
            'today_kwh': kwh_sum(today),
            'week_kwh': kwh_sum(week_start),
            'month_kwh': kwh_sum(month_start),
            'current_power_w': round(current_power_w, 2),
            'plug_count': plugs.count(),
            'plugs': plug_status,
            'top_devices': [{
                'device_id': str(d['device__id']),
                'device_name': d['device__name'],
                'total_kwh': round(d['total_kwh'] or 0, 4),
            } for d in top_devices],
        })


# ── Export endpoints ──────────────────────────────────────────────────────────

class EnergyExportView(APIView):
    """
    GET /api/houses/<house_id>/energy/export/
    Query params:
        format = csv | json  (default: csv)
        start, end
        plug_id (optional)
        device_id (optional)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, house_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err

        fmt = request.query_params.get('format', 'csv').lower()
        start, end = parse_date_range(request, default_days=30)
        plug_id = request.query_params.get('plug_id')
        device_id = request.query_params.get('device_id')

        qs = (
            EnergyReading.objects
            .filter(
                plug__house_id=house_id,
                recorded_at__date__gte=start,
                recorded_at__date__lte=end,
            )
            .select_related('plug', 'device')
            .order_by('recorded_at')
        )
        if plug_id:
            qs = qs.filter(plug_id=plug_id)
        if device_id:
            qs = qs.filter(device_id=device_id)

        filename_base = f"energy_{house_id}_{start}_{end}"

        if fmt == 'json':
            data = [{
                'id': str(r.id),
                'plug_id': str(r.plug_id),
                'plug_name': r.plug.name,
                'device_id': str(r.device_id) if r.device_id else None,
                'device_name': r.device.name if r.device else None,
                'voltage_v': r.voltage_v,
                'current_a': r.current_a,
                'power_w': r.power_w,
                'energy_kwh': r.energy_kwh,
                'recorded_at': r.recorded_at.isoformat(),
            } for r in qs]
            response = HttpResponse(
                json.dumps(data, indent=2),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename_base}.json"'
            return response

        # Default: CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename_base}.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'recorded_at', 'plug_id', 'plug_name', 'location',
            'device_id', 'device_name',
            'voltage_v', 'current_a', 'power_w', 'energy_kwh'
        ])
        for r in qs:
            writer.writerow([
                r.recorded_at.isoformat(),
                str(r.plug_id),
                r.plug.name,
                r.plug.location,
                str(r.device_id) if r.device_id else '',
                r.device.name if r.device else '',
                r.voltage_v,
                r.current_a,
                r.power_w,
                r.energy_kwh,
            ])
        return response


class EnergyReadingListView(APIView):
    """
    GET /api/houses/<house_id>/energy/readings/
    Raw readings with pagination.
    Query params: start, end, plug_id, device_id, limit (default 200), offset (default 0)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, house_id):
        membership, err = require_membership(house_id, request.user)
        if err:
            return err

        start, end = parse_date_range(request, default_days=1)
        plug_id = request.query_params.get('plug_id')
        device_id = request.query_params.get('device_id')
        limit = min(int(request.query_params.get('limit', 200)), 1000)
        offset = int(request.query_params.get('offset', 0))

        qs = EnergyReading.objects.filter(
            plug__house_id=house_id,
            recorded_at__date__gte=start,
            recorded_at__date__lte=end,
        ).select_related('plug', 'device').order_by('-recorded_at')

        if plug_id:
            qs = qs.filter(plug_id=plug_id)
        if device_id:
            qs = qs.filter(device_id=device_id)

        total = qs.count()
        readings = qs[offset:offset + limit]

        return Response({
            'total': total,
            'limit': limit,
            'offset': offset,
            'results': [{
                'id': str(r.id),
                'plug_id': str(r.plug_id),
                'plug_name': r.plug.name,
                'device_id': str(r.device_id) if r.device_id else None,
                'device_name': r.device.name if r.device else None,
                'voltage_v': r.voltage_v,
                'current_a': r.current_a,
                'power_w': r.power_w,
                'energy_kwh': r.energy_kwh,
                'recorded_at': r.recorded_at.isoformat(),
            } for r in readings],
        })
