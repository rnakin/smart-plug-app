from django.urls import path
from . import page_views

urlpatterns = [
    path('', page_views.device_list, name='page-device-list-global'),
]
