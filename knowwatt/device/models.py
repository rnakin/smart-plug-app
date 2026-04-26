from django.db import models

class EnergyLog(models.Model):
    plug = models.ForeignKey('SmartPlug', on_delete=models.CASCADE, related_name='energy_logs')
    watts = models.FloatField()
    kwh = models.FloatField()
    volts = models.FloatField()
    amps = models.FloatField()
    frequency = models.FloatField()
    pf = models.FloatField()
    timestamp = models.DateTimeField()

import uuid
from django.conf import settings
from house.models import House

#this is the table of smartplug that is produced
class ValidSmartPlug(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plug_code = models.CharField(max_length=64, unique=True,null=False)  # QR/manual code
    registered_at = models.DateTimeField(auto_now_add=True)
    blacklist = models.BooleanField(default=False)

# this is the table of smartplug entries use by the app
class SmartPlug(models.Model):#this is use by the app
    """Smart plug device registered to a house"""
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    house = models.ForeignKey(House, on_delete=models.CASCADE, null=True,related_name='plugs')
    room = models.ForeignKey(
        'house.Room',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plugs'
    )
    plug_code = models.CharField(max_length=64, unique=True)  # QR/manual code
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, default='')
    is_on = models.BooleanField(default=False)
    online_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='offline')
    is_verified = models.BooleanField(default=True, help_text='Whether the device is synced with the hardware registry')
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_plugs'
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Added fields from KnowWatt Spec
    relay_state = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    rssi = models.IntegerField(null=True, blank=True)
    uptime = models.IntegerField(default=0)
    active_uid = models.CharField(max_length=50, null=True, blank=True)

    # Alias for plug_id as per spec requirement for some lookups if needed
    @property
    def plug_id(self):
        return str(self.id)

    @property
    def current_device(self):
        session = self.sessions.filter(is_active=True).select_related('device').first()
        return session.device if session else None

    @property
    def active_session(self):
        """Return the active PlugSession (with device pre-fetched), or None."""
        return self.sessions.filter(is_active=True).select_related('device').first()

    @property
    def current_power_w(self):
        latest = self.energy_readings.order_by('-recorded_at').first()
        return round(latest.power_w, 1) if latest else 0.0

    class Meta:
        db_table = 'smart_plug'
        verbose_name = 'Smart Plug'
        verbose_name_plural = 'Smart Plugs'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.plug_code})"


class ElectricalDevice(models.Model):
    """Electrical appliance that can be plugged into a smart plug"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='devices')
    name = models.CharField(max_length=255)
    rated_power_watts = models.FloatField(help_text='Rated power in watts from spec')

    until_notify_minutes = models.IntegerField(
        null=True, blank=True,
        help_text='Auto power-off after this many minutes of continuous use (null = disabled)'
    )
    until_alert_minutes = models.IntegerField(
        null=True, blank=True,
        help_text='Auto power-off after this many minutes of continuous use (null = disabled)'
    )
    until_cutoff_minutes = models.IntegerField(
        null=True, blank=True,
        help_text='Auto power-off after this many minutes of continuous use (null = disabled)'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_devices'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'electrical_device'
        verbose_name = 'Electrical Device'
        verbose_name_plural = 'Electrical Devices'
        ordering = ['name']

    def __str__(self):
        return self.name



class NFCTag(models.Model):
    """NFC tag that identifies an electrical device when tapped on a smart plug"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag_uid = models.CharField(max_length=128, unique=True, help_text='Unique NFC tag UID')
    device = models.ForeignKey(
        ElectricalDevice,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='nfc_tags',
        help_text='Paired electrical device (null = unregistered tag)'
    )
    label = models.CharField(max_length=100, blank=True, default='', help_text='Optional label for this tag')
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_nfc_tags'
    )
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nfc_tag'
        verbose_name = 'NFC Tag'
        verbose_name_plural = 'NFC Tags'
        ordering = ['-registered_at']

    def __str__(self):
        device_name = self.device.name if self.device else 'Unregistered'
        return f"NFC {self.tag_uid} → {device_name}"


class PlugSession(models.Model):
    """Tracks when a device is plugged into a smart plug (via NFC scan)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plug = models.ForeignKey(SmartPlug, on_delete=models.CASCADE, related_name='sessions')
    device = models.ForeignKey(
        ElectricalDevice,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sessions'
    )
    nfc_tag = models.ForeignKey(
        NFCTag,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sessions'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'plug_session'
        verbose_name = 'Plug Session'
        verbose_name_plural = 'Plug Sessions'
        ordering = ['-started_at']

    def __str__(self):
        device_name = self.device.name if self.device else 'Unknown'
        return f"{device_name} @ {self.plug.name} ({self.started_at})"
