import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.contrib import messages
from .models import House, HouseMember, Room, Invite, generate_join_code
from .forms import HouseForm, HouseMemberInviteForm, HouseMemberRoleForm
from device.models import SmartPlug, ElectricalDevice
from energy.models import EnergyReading
from django.db.models import Sum
from django.utils import timezone
from datetime import date, timedelta


def get_user_membership(house, user):
    return HouseMember.objects.filter(house=house, user=user).first()


@login_required
def house_list(request):
    memberships = HouseMember.objects.filter(user=request.user).select_related('house')
    houses = []
    for m in memberships:
        houses.append({
            'house': m.house,
            'role': m.role,
            'member_count': HouseMember.objects.filter(house=m.house).count(),
            'plug_count': SmartPlug.objects.filter(house=m.house).count(),
        })
    
    # Received invites (incoming)
    incoming_invites = Invite.objects.filter(invitee=request.user, status='pending').select_related('house', 'inviter')
    
    # Sent invites (outgoing)
    sent_invites = Invite.objects.filter(inviter=request.user).select_related('house', 'invitee')

    return render(request, 'houses/house_list.html', {
        'houses': houses,
        'incoming_invites': incoming_invites,
        'sent_invites': sent_invites,
    })


@login_required
def house_create(request):
    if request.method == 'POST':
        house_name = request.POST.get('house_name')
        address = request.POST.get('address')
        emoji = request.POST.get('emoji', '🏠')
        lat = request.POST.get('lat')
        long = request.POST.get('long')
        join_code = request.POST.get('join_code')

        if not house_name or not address:
            messages.error(request, "Name and address are required.")
            return redirect('page-house-list')

        house = House(
            house_name=house_name,
            address=address,
            emoji=emoji
        )

        if lat:
            try: house.lat = float(lat)
            except ValueError: pass
        if long:
            try: house.long = float(long)
            except ValueError: pass

        if join_code:
            if House.objects.filter(join_code=join_code.upper()).exists():
                messages.error(request, f'Join code "{join_code}" is already taken.')
                return redirect('page-house-list')
            house.join_code = join_code.upper()
        else:
            # Generate unique join code
            while True:
                code = generate_join_code()
                if not House.objects.filter(join_code=code).exists():
                    house.join_code = code
                    break
        
        house.save()
        HouseMember.objects.create(house=house, user=request.user, role='owner')
        messages.success(request, f'House "{house.house_name}" created.')
        return redirect('page-house-detail', pk=house.pk)
    
    return redirect('page-house-list')


@login_required
def house_detail_main(request):
    """Entry point for the unified dashboard. Selects the last used house or the first available one."""
    # Try to get last used house from preferences
    last_house_id = None
    if hasattr(request.user, 'preferences'):
        last_house_id = request.user.preferences.last_house_id

    if last_house_id:
        membership = HouseMember.objects.filter(user=request.user, house_id=last_house_id).first()
        if membership:
            return redirect('page-house-detail', pk=last_house_id)

    # Fallback to first available
    membership = HouseMember.objects.filter(user=request.user).first()
    if not membership:
        messages.info(request, "You don't have any houses yet. Create or join one to get started!")
        return redirect('page-house-create')
    return redirect('page-house-detail', pk=membership.house.pk)


@login_required
def house_detail(request, pk):
    house = get_object_or_404(House, pk=pk)
    membership = get_user_membership(house, request.user)
    if not membership:
        messages.error(request, 'You are not a member of this house.')
        return redirect('page-house-list')

    # Update last used house preference
    from account.models import UserPreference
    pref, _ = UserPreference.objects.get_or_create(user=request.user)
    if pref.last_house_id != house.id:
        pref.last_house_id = house.id
        pref.save()

    # All user houses for the house selector
    user_houses = House.objects.filter(members__user=request.user)

    # Room Hierarchy
    rooms = house.rooms.all().prefetch_related('plugs')
    unassigned_plugs = house.plugs.filter(room__isnull=True)

    # Summary Stats
    total_power = 0.0
    all_plugs = house.plugs.all()
    
    # Simple Sync Check Simulation
    # In a real scenario, this would check against a hardware registry
    for plug in all_plugs:
        if not plug.is_verified:
            # Already marked as unverified
            pass
        elif len(plug.plug_code) < 4: # Simulated check
            plug.is_verified = False
            plug.save()

    for plug in all_plugs:
        latest = EnergyReading.objects.filter(plug=plug).order_by('-recorded_at').first()
        total_power += latest.power_w if latest else 0.0

    today = date.today()
    today_kwh = EnergyReading.objects.filter(
        plug__house=house,
        recorded_at__date=today,
    ).aggregate(total=Sum('energy_kwh'))['total'] or 0

    alerts = house.alert_events.filter(status='pending').order_by('-triggered_at')
    
    # Members for the management modal
    members = house.members.all().select_related('user')

    return render(request, 'home/app.html', {
        'active_house': house,
        'user_houses': user_houses,
        'membership': membership,
        'rooms': rooms,
        'unassigned_plugs': unassigned_plugs,
        'total_power': round(total_power, 1),
        'today_kwh': round(today_kwh, 2),
        'alerts': alerts,
        'members': members,
    })


@require_POST
@login_required
def create_room(request, pk):
    house = get_object_or_404(House, pk=pk)
    membership = get_user_membership(house, request.user)
    if membership and membership.role in ('owner', 'admin'):
        name = request.POST.get('name')
        emoji = request.POST.get('emoji', '🏠')
        if name:
            Room.objects.create(house=house, name=name, emoji=emoji)
            messages.success(request, f'Room "{name}" created.')
    return redirect('page-house-detail', pk=pk)


@require_POST
@login_required
def delete_room(request, pk, room_pk):
    house = get_object_or_404(House, pk=pk)
    membership = get_user_membership(house, request.user)
    if membership and membership.role in ('owner', 'admin'):
        room = get_object_or_404(Room, pk=room_pk, house=house)
        room_name = room.name
        room.delete()  # SET_NULL handles moving plugs to unassigned
        messages.success(request, f'Room "{room_name}" deleted. Plugs are now Unassigned.')
    return redirect('page-house-detail', pk=pk)


@require_POST
@login_required
def move_plug(request, pk):
    house = get_object_or_404(House, pk=pk)
    membership = get_user_membership(house, request.user)
    if membership and membership.role in ('owner', 'admin'):
        plug_id = request.POST.get('plug_id')
        room_id = request.POST.get('room_id')
        plug = get_object_or_404(SmartPlug, pk=plug_id, house=house)
        if room_id:
            room = get_object_or_404(Room, pk=room_id, house=house)
            plug.room = room
        else:
            plug.room = None
        plug.save()
        messages.success(request, f'Plug "{plug.name}" moved.')
    return redirect('page-house-detail', pk=pk)


@login_required
def house_edit(request, pk):
    house = get_object_or_404(House, pk=pk)
    membership = get_user_membership(house, request.user)
    if not membership or membership.role != 'owner':
        messages.error(request, 'Only the owner can edit this house.')
        return redirect('page-house-detail', pk=pk)

    if request.method == 'POST':
        # Update fields from POST data (since we're using custom modal forms)
        house.house_name = request.POST.get('house_name', house.house_name)
        house.address = request.POST.get('address', house.address)
        house.emoji = request.POST.get('emoji', house.emoji)
        
        lat = request.POST.get('lat')
        long = request.POST.get('long')
        if lat: house.lat = float(lat)
        if long: house.long = float(long)
        
        join_code = request.POST.get('join_code')
        if join_code and join_code != house.join_code:
            if not House.objects.filter(join_code=join_code).exists():
                house.join_code = join_code
            else:
                messages.error(request, f'Join code "{join_code}" is already in use.')

        house.save()
        messages.success(request, 'House updated.')
        return redirect('page-house-detail', pk=pk)
    
    return redirect('page-house-detail', pk=pk)


@require_POST
@login_required
def house_delete(request, pk):
    house = get_object_or_404(House, pk=pk)
    membership = get_user_membership(house, request.user)
    if not membership or membership.role != 'owner':
        messages.error(request, 'Only the owner can delete this house.')
        return redirect('page-house-list')
    house.delete()
    messages.success(request, 'House deleted.')
    return redirect('page-house-list')


@login_required
def house_members(request, pk):
    return redirect('page-house-detail', pk=pk)


@require_POST
@login_required
def house_member_invite(request, pk):
    house = get_object_or_404(House, pk=pk)
    membership = get_user_membership(house, request.user)
    if not membership or membership.role not in ('owner', 'admin'):
        messages.error(request, 'Only owner or admin can invite members.')
        return redirect('page-house-detail', pk=pk)

    email = request.POST.get('email')
    role = request.POST.get('role', 'member')

    if role == 'admin' and membership.role != 'owner':
        messages.error(request, 'Only owner can invite admins.')
        return redirect('page-house-detail', pk=pk)
    try:
        invited_user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, 'No user with that email exists.')
        return redirect('page-house-detail', pk=pk)
    
    if HouseMember.objects.filter(house=house, user=invited_user).exists():
        messages.error(request, 'User is already a member.')
        return redirect('page-house-detail', pk=pk)
    
    if Invite.objects.filter(house=house, invitee=invited_user, status='pending').exists():
        messages.error(request, 'User already has a pending invitation.')
        return redirect('page-house-detail', pk=pk)
    
    Invite.objects.create(
        house=house, 
        inviter=request.user, 
        invitee=invited_user, 
        role=role
    )
    messages.success(request, f'Invitation sent to {invited_user.username}.')
    return redirect('page-house-detail', pk=pk)


@require_POST
@login_required
def accept_invite(request, pk):
    invite = get_object_or_404(Invite, pk=pk, invitee=request.user, status='pending')
    
    # Create house membership
    HouseMember.objects.get_or_create(
        house=invite.house,
        user=request.user,
        defaults={'role': invite.role}
    )
    
    invite.status = 'accepted'
    invite.save()
    
    messages.success(request, f'You have joined {invite.house.house_name}.')
    return redirect('page-house-list')


@require_POST
@login_required
def deny_invite(request, pk):
    invite = get_object_or_404(Invite, pk=pk, invitee=request.user, status='pending')
    invite.status = 'denied'
    invite.save()
    
    messages.success(request, f'Invitation to {invite.house.house_name} denied.')
    return redirect('page-house-list')


@require_POST
@login_required
def house_member_update_role(request, pk, member_pk):
    house = get_object_or_404(House, pk=pk)
    membership = get_user_membership(house, request.user)
    target = get_object_or_404(HouseMember, pk=member_pk, house=house)

    if not membership or membership.role not in ('owner', 'admin'):
        messages.error(request, 'Insufficient permissions.')
        return redirect('page-house-detail', pk=pk)
    if target.role == 'owner':
        messages.error(request, 'Cannot change owner role.')
        return redirect('page-house-detail', pk=pk)
    if membership.role == 'admin' and target.role == 'admin':
        messages.error(request, 'Admin cannot change another admin.')
        return redirect('page-house-detail', pk=pk)

    new_role = request.POST.get('role')
    if new_role:
        if new_role == 'admin' and membership.role != 'owner':
            messages.error(request, 'Only owner can assign admin role.')
        else:
            target.role = new_role
            target.save()
            messages.success(request, f'Role updated to {new_role}.')
    return redirect('page-house-detail', pk=pk)


@require_POST
@login_required
def house_member_remove(request, pk, member_pk):
    house = get_object_or_404(House, pk=pk)
    membership = get_user_membership(house, request.user)
    target = get_object_or_404(HouseMember, pk=member_pk, house=house)

    if not membership or membership.role not in ('owner', 'admin'):
        messages.error(request, 'Insufficient permissions.')
        return redirect('page-house-detail', pk=pk)
    if target.role == 'owner':
        messages.error(request, 'Cannot remove owner.')
        return redirect('page-house-detail', pk=pk)
    if membership.role == 'admin' and target.role == 'admin':
        messages.error(request, 'Admin cannot remove another admin.')
        return redirect('page-house-detail', pk=pk)

    target.delete()
    messages.success(request, 'Member removed.')
    return redirect('page-house-detail', pk=pk)


@require_POST
@login_required
def house_leave(request, pk):
    house = get_object_or_404(House, pk=pk)
    membership = get_user_membership(house, request.user)
    if not membership:
        messages.error(request, 'You are not a member.')
        return redirect('page-house-list')
    if membership.role == 'owner':
        messages.error(request, 'Owner cannot leave. Delete or transfer ownership first.')
        return redirect('page-house-detail', pk=pk)
    membership.delete()
    messages.success(request, 'You have left the house.')
    return redirect('page-house-list')


@login_required
def house_join(request):
    if request.method == 'POST':
        code = request.POST.get('join_code', '').strip().upper()
        if not code:
            messages.error(request, 'Please enter a join code.')
            return redirect('page-house-list')
        try:
            house = House.objects.get(join_code=code)
        except House.DoesNotExist:
            messages.error(request, 'Invalid join code.')
            return redirect('page-house-list')
        if HouseMember.objects.filter(house=house, user=request.user).exists():
            messages.info(request, 'You are already a member of this house.')
            return redirect('page-house-detail', pk=house.pk)
        HouseMember.objects.create(house=house, user=request.user, role='member')
        messages.success(request, f'You joined "{house.house_name}"!')
        return redirect('page-house-detail', pk=house.pk)
    
    # GET request - we don't need the join page anymore as it's a modal
    return redirect('page-house-list')
