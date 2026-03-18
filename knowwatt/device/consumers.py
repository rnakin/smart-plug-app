"""
WebSocket consumers for real-time plug updates.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class PlugConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time plug status updates.
    
    Clients connect to: ws://host/ws/plug/{plug_code}/
    """

    async def connect(self):
        self.plug_code = self.scope['url_route']['kwargs']['plug_code']
        self.group_name = f'plug_{self.plug_code}'

        # Join group for this plug
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f'WebSocket connected to group: {self.group_name}')

    async def disconnect(self, close_code):
        # Leave group for this plug
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f'WebSocket disconnected from group: {self.group_name}')

    async def receive(self, text_data):
        # Handle incoming messages from client (if any)
        # For now, we only send updates to clients, not receive
        pass

    async def plug_update(self, event):
        """
        Handle messages sent to the plug group from the channel layer.
        This method is called when we send to group with type "plug.update".
        """
        # Send the event data to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'plug.update',
            'event': event.get('event'),
            'uid': event.get('uid'),
            'known': event.get('known'),
            'device_name': event.get('device_name'),
            'device_type': event.get('device_type'),
            'risk_level': event.get('risk_level'),
            'rated_watts': event.get('rated_watts'),
            'timestamp': event.get('timestamp'),
        }))
        logger.debug(f'Sent plug update to WebSocket: {event.get("event")}')
