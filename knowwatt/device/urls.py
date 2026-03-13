"""
Global device API endpoints (not scoped to a house).
Mounted under /api/ in knowwatt/urls.py
"""
from django.urls import path
from .views import NFCTagScanView

urlpatterns = [
    path('nfc/scan/', NFCTagScanView.as_view(), name='nfc-scan'),
]
