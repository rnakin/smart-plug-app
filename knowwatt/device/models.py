from django.db import models
import uuid
from django.conf import settings
from house.models import House


class SmartPlug(models.Model):
    """Smart plug device registered to a house"""
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='plugs')
    plug_code = models.CharField(max_length=64, unique=True)  # QR/manual code
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, default='')
    is_on = models.BooleanField(default=False)
    online_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='offline')
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_plugs'
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'smart_plug'
        verbose_name = 'Smart Plug'
        verbose_name_plural = 'Smart Plugs'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.plug_code})"


class ElectricalDevice(models.Model):
    """Electrical appliance that can be plugged into a smart plug"""
    RISK_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    DEVICE_TYPE_CHOICES = [
        ('appliance', 'Appliance'),
        ('entertainment', 'Entertainment'),
        ('lighting', 'Lighting'),
        ('hvac', 'HVAC'),
        ('kitchen', 'Kitchen'),
        ('office', 'Office'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='devices')
    name = models.CharField(max_length=255)
    device_type = models.CharField(max_length=30, choices=DEVICE_TYPE_CHOICES, default='other')
    rated_power_watts = models.FloatField(help_text='Rated power in watts from spec')
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES, default='low')
    auto_cutoff_minutes = models.IntegerField(
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
        return f"{self.name} ({self.device_type})"


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
