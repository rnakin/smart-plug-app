from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from datetime import date
from house.models import House, HouseMember
from device.models import SmartPlug
from energy.models import EnergyReading
from alert.models import AlertEvent


def index(request):
    if request.user.is_authenticated:
        return redirect('page-home')
    return render(request, 'index.html')


@login_required(login_url='/login/')
def dashboard_page(request):
    return redirect('page-home')


@login_required(login_url='/login/')
def home_page(request):
    memberships = HouseMember.objects.filter(user=request.user).select_related('house')
    houses = []
    for m in memberships:
        houses.append({
            'house': m.house,
            'role': m.role,
        })

    active_house = None
    plugs = []
    plug_data = []
    total_power = 0.0
    today_kwh = 0.0
    pending_alerts = 0
    rooms = {}

    if houses:
        # Allow selecting active house via ?house=<uuid>
        requested_house = request.GET.get('house')
        if requested_house:
            for h in houses:
                if str(h['house'].pk) == requested_house:
                    active_house = h['house']
                    break
        if not active_house:
            active_house = houses[0]['house']
        plugs = SmartPlug.objects.filter(house=active_house)

        for plug in plugs:
            latest = EnergyReading.objects.filter(plug=plug).order_by('-recorded_at').first()
            pw = latest.power_w if latest else 0.0
            total_power += pw
            active_session = plug.sessions.filter(is_active=True).select_related('device').first()
            device = active_session.device if active_session else None
            pd = {
                'plug': plug,
                'power_w': round(pw, 1),
                'device': device,
                'device_emoji': {
                    'kitchen': '🍳', 'appliance': '🔌', 'entertainment': '📺',
                    'lighting': '💡', 'hva': '❄️', 'hvac': '❄️', 'office': '💻', 'other': '🔌',
                }.get(device.device_type if device else '', '🔌'),
            }
            plug_data.append(pd)

        today = date.today()
        today_kwh = EnergyReading.objects.filter(
            plug__house=active_house, recorded_at__date=today,
        ).aggregate(t=Sum('energy_kwh'))['t'] or 0

        pending_alerts = AlertEvent.objects.filter(
            house=active_house, status='pending',
        ).count()

    # Group plugs by location for rendering
    grouped_plugs = {}
    for pd_item in plug_data:
        loc = pd_item['plug'].location or 'ไม่ระบุ'
        grouped_plugs.setdefault(loc, []).append(pd_item)

    # Sort locations: 'ไม่ระบุ' at the end
    sorted_locations = sorted(grouped_plugs.keys(), key=lambda x: (x == 'ไม่ระบุ', x))
    rooms = {loc: grouped_plugs[loc] for loc in sorted_locations}

    return render(request, 'home/app.html', {
        'houses': houses,
        'active_house': active_house,
        'active_house_role': next((h['role'] for h in houses if h['house'] == active_house), None) if active_house else None,
        'plug_data': plug_data,
        'total_power': round(total_power, 1),
        'today_kwh': round(today_kwh, 2),
        'pending_alerts': pending_alerts,
        'rooms': rooms,
        'plug_count': len(plug_data),
        'online_count': sum(1 for p in plug_data if p['plug'].online_status == 'online'),
        'on_count': sum(1 for p in plug_data if p['plug'].is_on),
    })
