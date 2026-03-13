"""
Energy API URL patterns — scoped to a house.
Included under /api/houses/<house_id>/ via house/urls.py
"""
from django.urls import path
from .views import (
    EnergyReadingIngestView,
    EnergyRealtimeView,
    EnergySummaryView,
    EnergyByDeviceView,
    EnergyByPlugView,
    EnergyHouseDashboardView,
    EnergyExportView,
    EnergyReadingListView,
)

urlpatterns = [
    # Ingest (firmware → server)
    path('energy/ingest/', EnergyReadingIngestView.as_view(), name='energy-ingest'),

    # Real-time current readings
    path('energy/realtime/', EnergyRealtimeView.as_view(), name='energy-realtime'),

    # Dashboard summary
    path('energy/dashboard/', EnergyHouseDashboardView.as_view(), name='energy-dashboard'),

    # Aggregated summaries
    path('energy/summary/', EnergySummaryView.as_view(), name='energy-summary'),
    path('energy/by-device/', EnergyByDeviceView.as_view(), name='energy-by-device'),
    path('energy/by-plug/', EnergyByPlugView.as_view(), name='energy-by-plug'),

    # Raw readings (paginated)
    path('energy/readings/', EnergyReadingListView.as_view(), name='energy-readings'),

    # Export
    path('energy/export/', EnergyExportView.as_view(), name='energy-export'),
]
