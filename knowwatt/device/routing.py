"""
WebSocket URL routing for device app.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/plug/(?P<plug_code>\w+)/$', consumers.PlugConsumer.as_asgi()),
]
