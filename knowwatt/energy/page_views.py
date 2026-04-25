from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Max
from django.db.models.functions import TruncDate
from django.contrib import messages
from .models import EnergyReading
from device.models import SmartPlug
from house.models import House, HouseMember


@login_required
def energy_dashboard(request, house_pk):
    house = get_object_or_404(House, pk=house_pk)
    membership = HouseMember.objects.filter(house=house, user=request.user).first()
    if not membership:
        messages.error(request, 'You are not a member.')
        return redirect('page-house-list')

    today = date.today()
    month_start = today.replace(day=1)
    week_start = today - timedelta(days=today.weekday())

    today_kwh = EnergyReading.objects.filter(
        plug__house=house, recorded_at__date=today,
    ).aggregate(t=Sum('energy_kwh'))['t'] or 0

    week_kwh = EnergyReading.objects.filter(
        plug__house=house, recorded_at__date__gte=week_start,
    ).aggregate(t=Sum('energy_kwh'))['t'] or 0

    month_kwh = EnergyReading.objects.filter(
        plug__house=house, recorded_at__date__gte=month_start,
    ).aggregate(t=Sum('energy_kwh'))['t'] or 0

    plugs = SmartPlug.objects.filter(house=house)
    plug_statuses = []
    current_power = 0.0
    for plug in plugs:
        latest = EnergyReading.objects.filter(plug=plug).order_by('-recorded_at').first()
        pw = latest.power_w if latest else 0.0
        current_power += pw
        plug_statuses.append({
            'plug': plug,
            'power_w': round(pw, 2),
            'latest': latest,
        })

    top_devices = (
        EnergyReading.objects
        .filter(plug__house=house, recorded_at__date__gte=month_start, device__isnull=False)
        .values('device__id', 'device__name')
        .annotate(total_kwh=Sum('energy_kwh'))
        .order_by('-total_kwh')[:5]
    )

    period = request.GET.get('period', 'daily')
    days_back = {'daily': 30, 'weekly': 84, 'monthly': 180}.get(period, 30)
    chart_start = today - timedelta(days=days_back)

    chart_data = (
        EnergyReading.objects
        .filter(plug__house=house, recorded_at__date__gte=chart_start, recorded_at__date__lte=today)
        .annotate(period=TruncDate('recorded_at'))
        .values('period')
        .annotate(
            total_kwh=Sum('energy_kwh'),
            avg_power_w=Avg('power_w'),
            peak_power_w=Max('power_w'),
        )
        .order_by('period')
    )

    by_plug_raw = (
        EnergyReading.objects
        .filter(plug__house=house, recorded_at__date__gte=chart_start)
        .values('plug__id', 'plug__name', 'plug__location')
        .annotate(
            total_kwh=Sum('energy_kwh'),
            avg_power_w=Avg('power_w'),
            peak_power_w=Max('power_w'),
        )
        .order_by('-total_kwh')
    )

    by_plug_max = max((row['total_kwh'] or 0) for row in by_plug_raw) if by_plug_raw else 1
    by_plug = [
        {
            'plug_name': row['plug__name'],
            'location': row['plug__location'] or 'Unassigned',
            'total_kwh': round(row['total_kwh'] or 0, 3),
            'avg_power_w': round(row['avg_power_w'] or 0, 1),
            'peak_power_w': round(row['peak_power_w'] or 0, 1),
            'bar_pct': round((row['total_kwh'] or 0) / by_plug_max * 100) if by_plug_max else 0,
        }
        for row in by_plug_raw
    ]

    return render(request, 'energy/energy_dashboard.html', {
        'house': house,
        'membership': membership,
        'today_kwh': round(today_kwh, 2),
        'week_kwh': round(week_kwh, 2),
        'month_kwh': round(month_kwh, 2),
        'current_power': round(current_power, 1),
        'plug_statuses': plug_statuses,
        'top_devices': [
            {'name': d['device__name'], 'total_kwh': round(d['total_kwh'] or 0, 3)}
            for d in top_devices
        ],
        'chart_data': [
            {
                'period': row['period'].isoformat() if row['period'] else '',
                'total_kwh': round(row['total_kwh'] or 0, 4),
            }
            for row in chart_data
        ],
        'by_plug': by_plug,
        'period': period,
    })
