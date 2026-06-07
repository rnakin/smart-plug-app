import json
import logging
import signal
import ssl
import sys
from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.db import close_old_connections
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from paho.mqtt import client as mqtt

from device.models import SmartPlug, PlugSession
from energy.models import EnergyReading
from device.mqtt_handlers import handle_nfc_event
from django.db import close_old_connections
logger = logging.getLogger(__name__)

TOPIC_STATUS = "status"
TOPIC_ENERGY = "energy_usage"
TOPIC_EVENT  = "event"


class Command(BaseCommand):
    help = 'Runs the MQTT subscriber daemon to sync smart plug state with the database'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = None
        self.shutdown_requested = False
        self.channel_layer = get_channel_layer()

    def handle(self, *args, **options):
        self.stdout.write("Starting KnowWatt MQTT Subscriber...")

        signal.signal(signal.SIGTERM, self._handle_exit)
        signal.signal(signal.SIGINT, self._handle_exit)

        self.client = mqtt.Client(
            client_id="knowwatt-daemon",
            protocol=mqtt.MQTTv5
        )
        self.client.on_connect    = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message    = self.on_message

        if getattr(settings, 'MQTT_USER', None) and getattr(settings, 'MQTT_PASSWORD', None):
            self.client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASSWORD)
        if getattr(settings, 'MQTT_USE_TLS', False):
            self.client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)

        try:
            self.client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, keepalive=60)
        except Exception as e:
            self.stderr.write(f"Could not connect to MQTT broker: {e}")
            sys.exit(1)

        self.client.loop_forever(retry_first_connection=True)

    def _handle_exit(self, signum, frame):
        self.stdout.write(f"Received signal {signum}. Shutting down cleanly...")
        self.shutdown_requested = True
        if self.client:
            self.client.disconnect()
        close_old_connections()
        sys.exit(0)

    # ------------------------------------------------------------------ #
    # Paho callbacks                                                       #
    # ------------------------------------------------------------------ #

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.stdout.write("Connected to MQTT Broker successfully.")
            client.subscribe([
                (TOPIC_STATUS, 1),
                (TOPIC_ENERGY, 1),
                (TOPIC_EVENT,  1),
            ])
            logger.info("Subscribed to %s, %s, %s with QoS 1",
                        TOPIC_STATUS, TOPIC_ENERGY, TOPIC_EVENT)
        else:
            self.stderr.write(f"Failed to connect, return code: {rc}")

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties=None):
        self.stdout.write(f"Disconnected — reason code: {reason_code}")
        if not self.shutdown_requested:
            logger.info("Unclean disconnect — loop_forever() will handle reconnection")

    def on_message(self, client, userdata, msg):
        topic_suffix = msg.topic.split('/')[-1]

        try:
            payload = msg.payload.decode('utf-8')
            data = json.loads(payload)
            self.stdout.write(f"MQTT Message Received: Topic: {msg.topic} | Payload: {payload}")
        except json.JSONDecodeError as e:
            self.stderr.write(f"JSON decode error on topic '{msg.topic}': {e}")
            return

        if topic_suffix == 'status':
            self._handle_status(data)
        elif topic_suffix == 'energy_usage':
            self._handle_energy(data)
        elif topic_suffix == 'event':
            self._handle_event(data)
        else:
            logger.debug("Unhandled topic suffix '%s' — ignoring", topic_suffix)

    # ------------------------------------------------------------------ #
    # Handlers                                                             #
    # ------------------------------------------------------------------ #

    def _handle_status(self, data):
        try:
            close_old_connections()
            plug_id = data.get('plug_id')
            if not plug_id:
                logger.warning("_handle_status: missing plug_id in payload")
                return

            self.stdout.write(f"Processing status for {plug_id}: {data}")

            # Fetch current plug state to detect hardware relay change
            plug = SmartPlug.objects.filter(plug_code=plug_id).first()
            if not plug:
                self.stdout.write(f"No SmartPlug found with plug_code {plug_id}")
                return

            was_on = plug.is_on
            relay_now = bool(data.get('relay', False))

            updated_count = SmartPlug.objects.filter(plug_code=plug_id).update(
                is_online=data.get('state') == 'online',
                online_status=data.get('state', 'offline'),
                uptime=data.get('uptime', 0),
                relay_state=relay_now,
                is_on=relay_now,
                rssi=data.get('rssi'),
                ip_address=data.get('ip'),
            )

            self.stdout.write(f"Successfully updated status for {plug_id} (relay={'on' if relay_now else 'off'})")

            # ── Hardware button turned relay OFF ──────────────────────
            if was_on and not relay_now:
                self.stdout.write(f"Hardware relay-off detected for {plug_id} — cancelling escalation timers")
                # End all active sessions and cancel timers
                ending_sessions = list(
                    PlugSession.objects.filter(plug=plug, is_active=True).values_list('id', 'device__name')
                )
                PlugSession.objects.filter(plug=plug, is_active=True).update(
                    is_active=False, ended_at=timezone.now()
                )
                for sid, dev_name in ending_sessions:
                    from alert.escalation import cancel_escalation
                    cancel_escalation(str(sid))
                    try:
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.group_send)(
                            f"house_{str(plug.house_id)}",
                            {
                                "type": "house.event",
                                "event": "session_ended",
                                "session_id": str(sid),
                                "plug_id": str(plug.id),
                                "plug_name": plug.name,
                                "device_name": dev_name or "Unknown",
                                "reason": "hardware_button",
                                "house_id": str(plug.house_id),
                            }
                        )
                    except Exception as e:
                        self.stderr.write(f"session_ended broadcast failed: {e}")

            # Broadcast via WebSockets
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"plug_{plug_id}",
                    {
                        "type": "plug.update",
                        "plug_id": str(plug.id),
                        "plug_code": plug_id,
                        "online_status": data.get('state', 'offline'),
                        "is_on": relay_now,
                        "current_power_w": plug.current_power_w,
                        "is_verified": True,
                        "current_device_name": plug.current_device.name if plug.current_device else None,
                    }
                )
                self.stdout.write(f"Broadcast sent to plug {plug_id}")
            except Exception as broadcast_error:
                logger.error(f"Broadcast failed: {broadcast_error}")
                self.stdout.write(f"Broadcast FAILED: {broadcast_error}")
                import traceback
                self.stdout.write(traceback.format_exc())

            logger.debug("Status updated for plug %s", plug_id)
        except Exception as e:
            self.stderr.write(f"Error in _handle_status: {e}")
            import traceback
            self.stderr.write(traceback.format_exc())
        finally:
            close_old_connections()

    def _handle_energy(self, data):
        try:
            close_old_connections()
            plug_id = data.get('plug_id')
            if not plug_id:
                logger.warning("_handle_energy: missing plug_id in payload")
                return

            self.stdout.write(f"Processing energy data for {plug_id}")
            try:
                plug = SmartPlug.objects.select_related('house').get(plug_code=plug_id)
            except SmartPlug.DoesNotExist:
                self.stdout.write(f"Discarding energy reading — SmartPlug '{plug_id}' does not exist")
                return

            ts_str = data.get('timestamp')
            if ts_str:
                naive_dt = datetime.fromisoformat(ts_str)
                aware_dt = timezone.make_aware(naive_dt)
            else:
                aware_dt = timezone.now()

            # Link to active session if one exists
            active_session = PlugSession.objects.filter(
                plug=plug, is_active=True
            ).select_related('device').first()

            EnergyReading.objects.create(
                plug=plug,
                session=active_session,
                device=active_session.device if active_session else None,
                power_w=data.get('watts', 0.0),
                energy_kwh=data.get('kwh', 0.0),
                voltage_v=data.get('volts', 0.0),
                current_a=data.get('amps', 0.0),
                recorded_at=aware_dt,
            )
            self.stdout.write(f"Successfully created EnergyReading for {plug_id}: {data.get('watts', 0.0)}W")

            # Broadcast via WebSockets
            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"plug_{plug_id}",
                    {
                        "type": "plug.update",
                        "event": "energy",
                        "plug_code": plug_id,
                        "plug_id": str(plug.id),
                        "watts": data.get('watts', 0.0),
                        "volts": data.get('volts', 0.0),
                        "amps": data.get('amps', 0.0),
                        "timestamp": aware_dt.isoformat(),
                    }
                )
            except Exception as broadcast_error:
                self.stderr.write(f"Broadcast failed: {broadcast_error}")

            logger.debug("EnergyReading created for plug %s", plug_id)
        except Exception as e:
            self.stderr.write(f"Error in _handle_energy: {e}")
            import traceback
            self.stderr.write(traceback.format_exc())
        finally:
            close_old_connections()

    def _handle_event(self, data):
        try:
            close_old_connections()
            plug_id    = data.get('plug_id')
            event_type = data.get('type')

            if not plug_id or not event_type:
                logger.warning("_handle_event: missing plug_id or type in payload")
                return

            if event_type in ('relay_on', 'relay_off'):
                self.stdout.write(f"Processing event {event_type} for {plug_id}")
                updated_count = SmartPlug.objects.filter(plug_code=plug_id).update(
                    relay_state=event_type == 'relay_on',
                    is_on=event_type == 'relay_on'
                )
                if updated_count == 0:
                    self.stdout.write(f"No SmartPlug found for event {event_type} on {plug_id}")
                else:
                    self.stdout.write(f"Successfully updated relay state for {plug_id}")
                    # Broadcast via WebSockets
                    try:
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.group_send)(
                            f"plug_{plug_id}",
                            {
                                "type": "plug.update",
                                "event": event_type,
                                "plug_code": plug_id,
                                "relay_state": event_type == 'relay_on',
                                "is_on": event_type == 'relay_on'
                            }
                        )
                    except Exception as broadcast_error:
                        self.stderr.write(f"Broadcast failed: {broadcast_error}")

            elif event_type == 'nfc_scan':
                # Delegate to the shared handler
                handle_nfc_event(client=self.client, topic=plug_id, payload_dict=data)
            else:
                logger.debug("Ignoring unknown event type '%s'", event_type)

        except Exception as e:
            self.stderr.write(f"Error in _handle_event: {e}")
        finally:
            close_old_connections()