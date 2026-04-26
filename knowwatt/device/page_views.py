from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import SmartPlug, ElectricalDevice, NFCTag, ValidSmartPlug
from .forms import SmartPlugForm, SmartPlugEditForm, ElectricalDeviceForm
from house.models import House, HouseMember


def check_membership(house, user, min_role=None):
    m = HouseMember.objects.filter(house=house, user=user).first()
    if not m:
        return None
    if min_role == 'owner' and m.role != 'owner':
        return None
    if min_role == 'admin' and m.role not in ('owner', 'admin'):
        return None
    return m


@login_required
def plug_create(request, house_pk):
    house = get_object_or_404(House, pk=house_pk)
    membership = check_membership(house, request.user, min_role='admin')
    if not membership:
        messages.error(request, 'Insufficient permissions.')
        return redirect('page-house-detail', pk=house_pk)

    if request.method == 'POST':
        name = request.POST.get('name')
        plug_code = request.POST.get('plug_code')
        room_id = request.POST.get('room')
        
        if not name or not plug_code:
            messages.error(request, 'Name and code are required.')
            return redirect('page-house-detail', pk=house_pk)

        if SmartPlug.objects.filter(plug_code=plug_code).exists():
            messages.error(request, f'Plug code "{plug_code}" is already registered.')
            return redirect('page-house-detail', pk=house_pk)

        if not ValidSmartPlug.objects.filter(plug_code__iexact=plug_code).exists():
            messages.error(request, f'Invalid plug code: "{plug_code}". Please use a genuine KnowWatt plug.')
            return redirect('page-house-detail', pk=house_pk)

        plug = SmartPlug(
            house=house,
            name=name,
            plug_code=plug_code,
            registered_by=request.user
        )
        
        if room_id:
            from house.models import Room
            plug.room = get_object_or_404(Room, pk=room_id, house=house)
            
        plug.save()
        messages.success(request, f'Plug "{plug.name}" registered successfully.')
        return redirect('page-house-detail', pk=house_pk)
    
    return redirect('page-house-detail', pk=house_pk)


@login_required
def plug_edit(request, house_pk, plug_pk):
    house = get_object_or_404(House, pk=house_pk)
    plug = get_object_or_404(SmartPlug, pk=plug_pk, house=house)
    membership = check_membership(house, request.user, min_role='admin')
    if not membership:
        messages.error(request, 'Insufficient permissions.')
        return redirect('page-house-detail', pk=house_pk)

    if request.method == 'POST':
        name = request.POST.get('name')
        room_id = request.POST.get('room_id')
        
        if name:
            plug.name = name
        
        if room_id:
            from house.models import Room
            room = get_object_or_404(Room, pk=room_id, house=house)
            plug.room = room
        elif room_id == "": # Unassigned
            plug.room = None
            
        plug.save()
        messages.success(request, f'Plug "{plug.name}" updated.')
        return redirect('page-house-detail', pk=house_pk)
    
    return redirect('page-house-detail', pk=house_pk)



@require_POST
@login_required
def plug_delete(request, house_pk, plug_pk):
    house = get_object_or_404(House, pk=house_pk)
    plug = get_object_or_404(SmartPlug, pk=plug_pk, house=house)
    membership = check_membership(house, request.user, min_role='admin')
    if not membership:
        messages.error(request, 'Insufficient permissions.')
        return redirect('page-house-detail', pk=house_pk)
    plug_name = plug.name
    plug.delete()
    messages.success(request, f'Plug "{plug_name}" removed.')
    return redirect('page-house-detail', pk=house_pk)


@require_POST
@login_required
def plug_control(request, house_pk, plug_pk):
    house = get_object_or_404(House, pk=house_pk)
    plug = get_object_or_404(SmartPlug, pk=plug_pk, house=house)
    membership = check_membership(house, request.user)
    if not membership:
        messages.error(request, 'Insufficient permissions.')
        return redirect('page-house-detail', pk=house_pk)
    if membership.role == 'guest':
        messages.error(request, 'Guests cannot control devices.')
        return redirect('page-house-detail', pk=house_pk)

    action = request.POST.get('action')
    if action == 'on':
        plug.is_on = True
        plug.save()
        messages.success(request, f'{plug.name} turned ON.')
    elif action == 'off':
        plug.is_on = False
        plug.save()
        messages.success(request, f'{plug.name} turned OFF.')
    return redirect('page-house-detail', pk=house_pk)


@login_required
def device_list(request, house_pk=None):
    user_memberships = HouseMember.objects.filter(user=request.user).select_related('house')
    user_houses = [m.house for m in user_memberships]
    
    if not user_houses:
        messages.info(request, "You don't have any houses yet.")
        return redirect('page-house-list')

    # Selected house from URL or query param or first available
    selected_house_id = house_pk or request.GET.get('house')
    house = None
    if selected_house_id:
        house = next((h for h in user_houses if str(h.id) == str(selected_house_id)), None)
    
    if not house:
        house = user_houses[0]

    membership = HouseMember.objects.filter(house=house, user=request.user).first()
    
    devices = ElectricalDevice.objects.filter(house=house).prefetch_related('nfc_tags')
    
    # Organize tags by device for easier template rendering
    device_tags = {}
    for device in devices:
        device_tags[device.id] = list(device.nfc_tags.all())

    return render(request, 'devices/device_list.html', {
        'house': house,
        'user_houses': user_houses,
        'membership': membership,
        'devices': devices,
        'device_tags': device_tags,
        'active_house': house, # For base.html
    })


@login_required
def device_create(request, house_pk):
    house = get_object_or_404(House, pk=house_pk)
    membership = check_membership(house, request.user, min_role='admin')
    if not membership:
        messages.error(request, 'Insufficient permissions.')
        return redirect('page-device-list', house_pk=house_pk)

    if request.method == 'POST':
        form = ElectricalDeviceForm(request.POST)
        if form.is_valid():
            device = form.save(commit=False)
            device.house = house
            device.created_by = request.user
            device.save()
            messages.success(request, f'Device "{device.name}" created.')
            return redirect('page-device-list', house_pk=house_pk)
    else:
        form = ElectricalDeviceForm()
    return render(request, 'devices/device_form.html', {
        'form': form, 'house': house, 'editing': False,
    })


@login_required
def device_edit(request, house_pk, device_pk):
    house = get_object_or_404(House, pk=house_pk)
    device = get_object_or_404(ElectricalDevice, pk=device_pk, house=house)
    membership = check_membership(house, request.user, min_role='admin')
    if not membership:
        messages.error(request, 'Insufficient permissions.')
        return redirect('page-device-list', house_pk=house_pk)

    if request.method == 'POST':
        form = ElectricalDeviceForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            messages.success(request, 'Device updated.')
            return redirect('page-device-list', house_pk=house_pk)
    else:
        form = ElectricalDeviceForm(instance=device)
    
    # Get unassigned NFC tags for this house
    # Unassigned tags are those where device is None
    # We filter by registered_by as a proxy for house if no direct house link on tag
    # or better, just get all where device is None and the user is a member of the house
    unassigned_tags = NFCTag.objects.filter(device__isnull=True).order_by('-registered_at')

    return render(request, 'devices/device_form.html', {
        'form': form, 'house': house, 'device': device, 'editing': True,
        'unassigned_tags': unassigned_tags,
    })


@require_POST
@login_required
def device_delete(request, house_pk, device_pk):
    house = get_object_or_404(House, pk=house_pk)
    device = get_object_or_404(ElectricalDevice, pk=device_pk, house=house)
    membership = check_membership(house, request.user, min_role='admin')
    if not membership:
        messages.error(request, 'Insufficient permissions.')
        return redirect('page-device-list', house_pk=house_pk)
    device_name = device.name
    device.delete()
    messages.success(request, f'Device "{device_name}" deleted.')
    return redirect('page-device-list', house_pk=house_pk)
