import os
import json
import logging
import time
import signal
import sys

import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from django.conf import settings
import django

logger = logging.getLogger(__name__)

# MQTT configuration from environment variables
MQTT_HOST = os.environ.get('MQTT_HOST', '')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 8883))
MQTT_USER = os.environ.get('MQTT_USER', '')
MQTT_PASS = os.environ.get('MQTT_PASS', '')
MQTT_USE_TLS = os.environ.get('MQTT_USE_TLS', 'true').lower() == 'true'

# Reconnection settings
MAX_RECONNECT_DELAY = 60  # seconds
INITIAL_RECONNECT_DELAY = 1


class Command(BaseCommand):
    help = 'MQTT subscriber for NFC tag events from smart plugs'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = None
        self.reconnect_delay = INITIAL_RECONNECT_DELAY
        self.should_stop = False

    def handle(self, *args, **options):
        """Main entry point for the management command."""
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.stdout.write(self.style.SUCCESS('Starting MQTT subscriber...'))
        
        # Create MQTT client
        self.client = mqtt.Client(client_id='django_mqtt_subscriber')
        
        # Set up authentication
        if MQTT_USER:
            self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        
        # Set up TLS if enabled
        if MQTT_USE_TLS:
            self.client.tls_set()
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_log = self._on_log
        
        # Connect to broker
        self._connect()
        
        # Start loop - runs forever
        try:
            self.client.loop_forever()
        except Exception as e:
            logger.error(f'Loop error: {e}')
            raise

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.stdout.write(self.style.WARNING('Received shutdown signal, stopping...'))
        self.should_stop = True
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
        sys.exit(0)

    def _connect(self):
        """Connect to MQTT broker with retry logic."""
        try:
            logger.info(f'Connecting to MQTT broker at {MQTT_HOST}:{MQTT_PORT}')
            self.stdout.write(f'Connecting to MQTT broker at {MQTT_HOST}:{MQTT_PORT}')
            result = self.client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.reconnect_delay = INITIAL_RECONNECT_DELAY
                logger.info('Connected to MQTT broker')
                self.stdout.write(self.style.SUCCESS('Connected to MQTT broker'))
            else:
                raise Exception(f'Connection failed with result code: {result}')
        except Exception as e:
            logger.error(f'Failed to connect to MQTT broker: {e}')
            self.stdout.write(self.style.ERROR(f'Failed to connect: {e}'))
            self._schedule_reconnect()

    def _schedule_reconnect(self):
        """Schedule a reconnection attempt with exponential backoff."""
        if self.should_stop:
            return
        logger.info(f'Scheduling reconnect in {self.reconnect_delay} seconds')
        self.stdout.write(f'Scheduling reconnect in {self.reconnect_delay} seconds...')
        time.sleep(self.reconnect_delay)
        self.reconnect_delay = min(self.reconnect_delay * 2, MAX_RECONNECT_DELAY)
        self._connect()

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            logger.info('MQTT connection established')
            self.stdout.write(self.style.SUCCESS('MQTT connection established'))
            # Subscribe to plug events
            topic = '+/event'
            client.subscribe(topic)
            logger.info(f'Subscribed to topic: {topic}')
            self.stdout.write(f'Subscribed to topic: {topic}')
        elif rc == 1:
            logger.error('Connection refused - incorrect protocol version')
            self.stdout.write(self.style.ERROR('Connection refused - incorrect protocol version'))
        elif rc == 2:
            logger.error('Connection refused - invalid client identifier')
            self.stdout.write(self.style.ERROR('Connection refused - invalid client identifier'))
        elif rc == 3:
            logger.error('Connection refused - server unavailable')
            self.stdout.write(self.style.ERROR('Connection refused - server unavailable'))
        elif rc == 4:
            logger.error('Connection refused - bad username or password')
            self.stdout.write(self.style.ERROR('Connection refused - bad username or password'))
        elif rc == 5:
            logger.error('Connection refused - not authorized')
            self.stdout.write(self.style.ERROR('Connection refused - not authorized'))
        else:
            logger.error(f'Connection failed with code: {rc}')
            self.stdout.write(self.style.ERROR(f'Connection failed with code: {rc}'))

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker."""
        if rc != 0:
            logger.warning(f'Disconnected from MQTT broker with return code: {rc}')
            self.stdout.write(self.style.WARNING(f'Disconnected from MQTT broker (rc: {rc})'))
            self._schedule_reconnect()
        else:
            logger.info('Disconnected from MQTT broker gracefully')
            self.stdout.write('Disconnected from MQTT broker gracefully')

    def _on_message(self, client, userdata, msg):
        """Callback when a message is received."""
        try:
            topic = msg.topic
            payload = msg.payload
            
            logger.info(f'Received message on topic: {topic}')
            self.stdout.write(f'Received message on topic: {topic}')
            
            # Import here to avoid circular imports - will be created in TASK 2
            from device.mqtt_handlers import handle_nfc_event
            
            # Call the handler with the client for publishing back
            handle_nfc_event(client, topic, payload)
            
        except Exception as e:
            logger.error(f'Error processing message: {e}')
            self.stdout.write(self.style.ERROR(f'Error processing message: {e}'))
        finally:
            # Close old database connections to prevent stale connections
            # (paho-mqtt runs callbacks in a separate thread)
            import django.db
            django.db.close_old_connections()
            logger.debug('Closed old database connections')

    def _on_log(self, client, userdata, level, string):
        """Callback for MQTT client logs."""
        # Only log warnings and errors to avoid flooding logs
        if level >= mqtt.MQTT_LOG_WARNING:
            logger.log(
                mqtt.MQTT_LOG_WARNING if level == mqtt.MQTT_LOG_WARNING else mqtt.MQTT_LOG_ERR,
                f'MQTT: {string}'
            )
