import json
import paho.mqtt.publish as publish
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from .models import SmartPlug

@require_POST
def publish_command(request, plug_id):
    """
    Publishes a turn_on/turn_off command to MQTT and returns a pending HTMX state.
    """
    action = request.POST.get('action')
    if action not in ['turn_on', 'turn_off']:
        return HttpResponse("Invalid action", status=400)

    # Topic: <plug_id>/command
    topic = f"{plug_id}/command"
    payload = json.dumps({"command": action})

    auth = None
    if settings.MQTT_USER and settings.MQTT_PASSWORD:
        auth = {'username': settings.MQTT_USER, 'password': settings.MQTT_PASSWORD}

    # Stateless publish
    publish.single(
        topic,
        payload=payload,
        hostname=settings.MQTT_BROKER,
        port=settings.MQTT_PORT,
        auth=auth,
        qos=1
    )

    # Return the pending state partial
    return render(request, 'device/partials/_button_pending.html', {
        'plug_id': plug_id,
        'action': action
    })

def relay_status(request, plug_id):
    """
    Polling endpoint to check if the relay state matches the desired state.
    """
    plug = get_object_or_404(SmartPlug, plug_id=plug_id)
    # The frontend expects a certain state after a command. 
    # For simplicity, we just return the confirmed button if it matches the current DB state,
    # or keep returning pending if not.
    # The _button_confirmed template will decide what label to show based on plug.relay_state.
    
    # In a real scenario, we might want to know what we are waiting FOR.
    # But as per spec, we just return _button_pending or _button_confirmed.
    
    # If the user just clicked "Turn On", we wait until relay_state is True.
    # If "Turn Off", wait until False.
    # However, the spec says "returns the spinner fragment" or "final button fragment".
    
    # Logic: if the UI is polling, it means a command was sent. 
    # We'll just return the confirmed state once the DB reflects ANY state, 
    # or more specifically, we can just return confirmed and let the template render the button.
    # If we want to stay in "pending" until the hardware confirms, we'd need to know the target state.
    # The spec says: "Confirmed: returns the final button fragment... HTMX stops polling"
    
    target_state = request.GET.get('target') # Optional: if we want to be precise
    
    # As per spec: "The polling endpoint queries SmartPlug.relay_state from the DB"
    # We will assume that if we are here, we are waiting for a change.
    # To keep it simple and robust, if we are in this view, we check if the current DB state
    # matches what we'd expect after the action. 
    # But since the "Confirmed" state is just the normal button, 
    # we can return it when the state matches or just return it to stop polling.
    
    # Let's check if the current relay_state matches the 'target' passed in query params.
    current_state = "turn_on" if plug.relay_state else "turn_off"
    
    if target_state and current_state != target_state:
        return render(request, 'device/partials/_button_pending.html', {
            'plug_id': plug_id,
            'action': target_state
        })

    return render(request, 'device/partials/_button_confirmed.html', {
        'plug': plug
    })
