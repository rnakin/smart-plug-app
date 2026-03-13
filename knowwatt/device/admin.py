from django.contrib import admin
from .models import SmartPlug, ElectricalDevice, NFCTag, PlugSession

@admin.register(SmartPlug)
class SmartPlugAdmin(admin.ModelAdmin):
    list_display = ('name', 'plug_code', 'house', 'is_on', 'online_status', 'registered_at')
    list_filter = ('is_on', 'online_status')
    search_fields = ('name', 'plug_code')

@admin.register(ElectricalDevice)
class ElectricalDeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'device_type', 'rated_power_watts', 'risk_level', 'house')
    list_filter = ('device_type', 'risk_level')
    search_fields = ('name',)

@admin.register(NFCTag)
class NFCTagAdmin(admin.ModelAdmin):
    list_display = ('tag_uid', 'device', 'label', 'registered_at')
    search_fields = ('tag_uid', 'label')

@admin.register(PlugSession)
class PlugSessionAdmin(admin.ModelAdmin):
    list_display = ('plug', 'device', 'started_at', 'ended_at', 'is_active')
    list_filter = ('is_active',)
