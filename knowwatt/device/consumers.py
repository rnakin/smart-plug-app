"""
WebSocket consumers for real-time plug updates.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class PlugConsumer(AsyncWebsocketConsumer):

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
        await self.send(text_data=json.dumps(event))
        logger.debug(f'Sent plug update to WebSocket: {event.get("type")}')

class HouseConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.house_id = self.scope['url_route']['kwargs']['house_id']
        self.group_name = f'house_{self.house_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def house_event(self, event):
        await self.send(text_data=json.dumps(event))