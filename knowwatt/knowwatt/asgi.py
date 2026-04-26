import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'knowwatt.settings')
django.setup()

from device.consumers import PlugConsumer  

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter([
        path("ws/plug/<str:plug_code>/", PlugConsumer.as_asgi()),
    ]),
})