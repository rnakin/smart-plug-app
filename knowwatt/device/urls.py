"""
Global device API endpoints (not scoped to a house).
Mounted under /api/ in knowwatt/urls.py
"""

from django.urls import path
from .views import (
    NFCTagScanView,
    UnregisteredNFCTagsView,
    NFCTagRegisterView,
    nfc_register_from_popup,
)


urlpatterns = [
    path('nfc/scan/', NFCTagScanView.as_view(), name='nfc-scan'),
    path('nfc/unregistered/', UnregisteredNFCTagsView.as_view(), name='nfc-unregistered'),
    path('nfc/<str:tag_uid>/register/', NFCTagRegisterView.as_view(), name='nfc-register'),
    path('houses/<uuid:house_id>/nfc/register/', nfc_register_from_popup, name='nfc-register-popup'),  
]