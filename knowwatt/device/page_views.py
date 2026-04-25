from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import SmartPlug, ElectricalDevice, NFCTag
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
        form = SmartPlugForm(request.POST)
        if form.is_valid():
            plug = form.save(commit=False)
            plug.house = house
            plug.registered_by = request.user
            plug.save()
            messages.success(request, f'Plug "{plug.name}" added.')
            return redirect('page-house-detail', pk=house_pk)
    else:
        form = SmartPlugForm()
    return render(request, 'devices/plug_form.html', {
        'form': form, 'house': house, 'editing': False,
    })


@login_required
def plug_edit(request, house_pk, plug_pk):
    house = get_object_or_404(House, pk=house_pk)
    plug = get_object_or_404(SmartPlug, pk=plug_pk, house=house)
    membership = check_membership(house, request.user, min_role='admin')
    if not membership:
        messages.error(request, 'Insufficient permissions.')
        return redirect('page-house-detail', pk=house_pk)

    if request.method == 'POST':
        form = SmartPlugEditForm(request.POST, instance=plug)
        if form.is_valid():
            form.save()
            messages.success(request, 'Plug updated.')
            return redirect('page-house-detail', pk=house_pk)
    else:
        form = SmartPlugEditForm(instance=plug)
    return render(request, 'devices/plug_form.html', {
        'form': form, 'house': house, 'plug': plug, 'editing': True,
    })


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
def device_list(request, house_pk):
    house = get_object_or_404(House, pk=house_pk)
    membership = check_membership(house, request.user)
    if not membership:
        messages.error(request, 'You are not a member.')
        return redirect('page-house-list')

    devices = ElectricalDevice.objects.filter(house=house)
    nfc_tags = NFCTag.objects.filter(device__house=house).select_related('device')
    return render(request, 'devices/device_list.html', {
        'house': house,
        'membership': membership,
        'devices': devices,
        'nfc_tags': nfc_tags,
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
    return render(request, 'devices/device_form.html', {
        'form': form, 'house': house, 'device': device, 'editing': True,
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
