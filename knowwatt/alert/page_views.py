from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from .models import AlertRule, AlertEvent
from .forms import AlertRuleForm
from device.models import SmartPlug, ElectricalDevice
from house.models import House, HouseMember


@login_required
def alert_event_list(request, house_pk):
    house = get_object_or_404(House, pk=house_pk)
    membership = HouseMember.objects.filter(house=house, user=request.user).first()
    if not membership:
        messages.error(request, 'You are not a member.')
        return redirect('page-house-list')

    status_filter = request.GET.get('status', 'pending')
    qs = AlertEvent.objects.filter(house=house).select_related('plug', 'device', 'rule')
    if status_filter != 'all':
        qs = qs.filter(status=status_filter)

    return render(request, 'alerts/alert_event_list.html', {
        'house': house,
        'membership': membership,
        'events': qs[:50],
        'status_filter': status_filter,
    })


@require_POST
@login_required
def alert_event_action(request, house_pk, event_pk):
    house = get_object_or_404(House, pk=house_pk)
    membership = HouseMember.objects.filter(house=house, user=request.user).first()
    if not membership:
        messages.error(request, 'You are not a member.')
        return redirect('page-house-list')

    event = get_object_or_404(AlertEvent, pk=event_pk, house=house)
    action = request.POST.get('action')

    if action == 'acknowledge':
        event.status = 'acknowledged'
        event.resolved_at = timezone.now()
        event.save()
        messages.success(request, 'Alert acknowledged.')
    elif action == 'dismiss':
        event.status = 'dismissed'
        event.resolved_at = timezone.now()
        event.save()
        messages.success(request, 'Alert dismissed.')
    elif action == 'snooze':
        event.status = 'snoozed'
        event.snooze_until = timezone.now() + timedelta(minutes=30)
        event.save()
        messages.success(request, 'Alert snoozed.')
    elif action == 'auto_off':
        if event.plug:
            event.plug.is_on = False
            event.plug.save()
        event.status = 'acknowledged'
        event.resolved_at = timezone.now()
        event.save()
        messages.success(request, 'Plug turned off and alert acknowledged.')

    return redirect('page-alert-events', house_pk=house_pk)


@login_required
def alert_rule_list(request, house_pk):
    house = get_object_or_404(House, pk=house_pk)
    membership = HouseMember.objects.filter(house=house, user=request.user).first()
    if not membership:
        messages.error(request, 'You are not a member.')
        return redirect('page-house-list')

    rules = AlertRule.objects.filter(house=house).select_related('plug', 'device')
    return render(request, 'alerts/alert_rule_list.html', {
        'house': house,
        'membership': membership,
        'rules': rules,
    })


@login_required
def alert_rule_create(request, house_pk):
    house = get_object_or_404(House, pk=house_pk)
    membership = HouseMember.objects.filter(house=house, user=request.user).first()
    if not membership or membership.role not in ('owner', 'admin'):
        messages.error(request, 'Only owner or admin can create alert rules.')
        return redirect('page-alert-rules', house_pk=house_pk)

    if request.method == 'POST':
        form = AlertRuleForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.house = house
            rule.created_by = request.user
            rule.save()
            messages.success(request, 'Alert rule created.')
            return redirect('page-alert-rules', house_pk=house_pk)
    else:
        form = AlertRuleForm()
        form.fields['plug'].queryset = SmartPlug.objects.filter(house=house)
        form.fields['device'].queryset = ElectricalDevice.objects.filter(house=house)

    return render(request, 'alerts/alert_rule_form.html', {
        'form': form, 'house': house, 'editing': False,
    })


@login_required
def alert_rule_edit(request, house_pk, rule_pk):
    house = get_object_or_404(House, pk=house_pk)
    rule = get_object_or_404(AlertRule, pk=rule_pk, house=house)
    membership = HouseMember.objects.filter(house=house, user=request.user).first()
    if not membership or membership.role not in ('owner', 'admin'):
        messages.error(request, 'Only owner or admin can edit alert rules.')
        return redirect('page-alert-rules', house_pk=house_pk)

    if request.method == 'POST':
        form = AlertRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Alert rule updated.')
            return redirect('page-alert-rules', house_pk=house_pk)
    else:
        form = AlertRuleForm(instance=rule)
        form.fields['plug'].queryset = SmartPlug.objects.filter(house=house)
        form.fields['device'].queryset = ElectricalDevice.objects.filter(house=house)

    return render(request, 'alerts/alert_rule_form.html', {
        'form': form, 'house': house, 'rule': rule, 'editing': True,
    })


@require_POST
@login_required
def alert_rule_delete(request, house_pk, rule_pk):
    house = get_object_or_404(House, pk=house_pk)
    rule = get_object_or_404(AlertRule, pk=rule_pk, house=house)
    membership = HouseMember.objects.filter(house=house, user=request.user).first()
    if not membership or membership.role not in ('owner', 'admin'):
        messages.error(request, 'Only owner or admin can delete alert rules.')
        return redirect('page-alert-rules', house_pk=house_pk)
    rule.delete()
    messages.success(request, 'Alert rule deleted.')
    return redirect('page-alert-rules', house_pk=house_pk)
