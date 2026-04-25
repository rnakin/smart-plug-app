from django.urls import path
from . import page_views

urlpatterns = [
    path('energy/', page_views.energy_dashboard, name='page-energy-dashboard'),
]
