from django.urls import path
from . import page_views

urlpatterns = [
    path('plugs/create/', page_views.plug_create, name='page-plug-create'),
    path('plugs/<uuid:plug_pk>/edit/', page_views.plug_edit, name='page-plug-edit'),
    path('plugs/<uuid:plug_pk>/delete/', page_views.plug_delete, name='page-plug-delete'),
    path('plugs/<uuid:plug_pk>/control/', page_views.plug_control, name='page-plug-control'),
    path('devices/', page_views.device_list, name='page-device-list'),
    path('devices/create/', page_views.device_create, name='page-device-create'),
    path('devices/<uuid:device_pk>/edit/', page_views.device_edit, name='page-device-edit'),
    path('devices/<uuid:device_pk>/delete/', page_views.device_delete, name='page-device-delete'),
]
