"""
URL patterns scoped to a house.
Included under /api/houses/<house_id>/ by house/urls.py
"""
from django.urls import path
from .views import (
    SmartPlugListCreateView,
    SmartPlugDetailView,
    SmartPlugControlView,
    ElectricalDeviceListCreateView,
    ElectricalDeviceDetailView,
    NFCTagListView,
    NFCTagRegisterView,
    NFCTagDetailView,
)

urlpatterns = [
    # Smart Plugs
    path('plugs/', SmartPlugListCreateView.as_view(), name='plug-list-create'),
    path('plugs/<uuid:plug_id>/', SmartPlugDetailView.as_view(), name='plug-detail'),
    path('plugs/<uuid:plug_id>/control/', SmartPlugControlView.as_view(), name='plug-control'),

    # Electrical Devices
    path('devices/', ElectricalDeviceListCreateView.as_view(), name='device-list-create'),
    path('devices/<uuid:device_id>/', ElectricalDeviceDetailView.as_view(), name='device-detail'),

    # NFC Tags (house-scoped)
    path('nfc/', NFCTagListView.as_view(), name='nfc-list'),
    path('nfc/register/', NFCTagRegisterView.as_view(), name='nfc-register'),
    path('nfc/<uuid:tag_id>/', NFCTagDetailView.as_view(), name='nfc-detail'),
]
