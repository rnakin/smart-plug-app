from django.db import models
import uuid
from django.conf import settings
from device.models import SmartPlug, ElectricalDevice
from house.models import House


class AlertRule(models.Model):
    """
    User-defined alert rule for a device or plug.
    Triggers an AlertEvent when conditions are met.
    """
    TRIGGER_CHOICES = [
        ('power_above', 'Power above threshold (W)'),
        ('power_below', 'Power below threshold (W)'),
        ('duration_above', 'Device on longer than N minutes'),
        ('device_plugged_in', 'Device plugged in (NFC detected)'),
        ('device_unplugged', 'Device unplugged / session ended'),
        ('offline', 'Plug went offline'),
    ]
    ACTION_CHOICES = [
        ('notify', 'Notify only'),
        ('auto_off', 'Auto power-off plug'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='alert_rules')
    plug = models.ForeignKey(
        SmartPlug, on_delete=models.CASCADE, null=True, blank=True,
        related_name='alert_rules',
        help_text='Scope to a specific plug (null = all plugs in house)'
    )
    device = models.ForeignKey(
        ElectricalDevice, on_delete=models.CASCADE, null=True, blank=True,
        related_name='alert_rules',
        help_text='Scope to a specific device (null = any device)'
    )
    trigger = models.CharField(max_length=30, choices=TRIGGER_CHOICES)
    threshold_value = models.FloatField(
        null=True, blank=True,
        help_text='Threshold value (watts for power rules, minutes for duration rules)'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='notify')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='created_alert_rules'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'alert_rule'
        verbose_name = 'Alert Rule'
        verbose_name_plural = 'Alert Rules'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.trigger} → {self.action} ({self.house.house_name})"


class AlertEvent(models.Model):
    """
    An alert that was triggered by a rule.
    Users can acknowledge, snooze, or dismiss it.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending — awaiting user response'),
        ('acknowledged', 'Acknowledged'),
        ('snoozed', 'Snoozed — remind later'),
        ('dismissed', 'Dismissed'),
        ('auto_resolved', 'Auto-resolved by system'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='events')
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='alert_events')
    plug = models.ForeignKey(
        SmartPlug, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='alert_events'
    )
    device = models.ForeignKey(
        ElectricalDevice, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='alert_events'
    )

    title = models.CharField(max_length=255)
    message = models.TextField()
    trigger_value = models.FloatField(
        null=True, blank=True,
        help_text='Actual value that triggered the alert (e.g. actual watts)'
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    triggered_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    snooze_until = models.DateTimeField(null=True, blank=True)

    # Push notification tracking
    push_sent = models.BooleanField(default=False)
    push_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'alert_event'
        verbose_name = 'Alert Event'
        verbose_name_plural = 'Alert Events'
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['house', 'status', 'triggered_at']),
        ]

    def __str__(self):
        return f"[{self.status}] {self.title} @ {self.triggered_at}"


class UserPushToken(models.Model):
    """
    FCM / APNs push notification token for a user device.
    One user can have multiple tokens (multiple devices).
    """
    PLATFORM_CHOICES = [
        ('fcm', 'Firebase Cloud Messaging (Android/Web)'),
        ('apns', 'Apple Push Notification Service (iOS)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='push_tokens'
    )
    token = models.TextField(unique=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, default='fcm')
    device_label = models.CharField(max_length=100, blank=True, default='')
    is_active = models.BooleanField(default=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'user_push_token'
        verbose_name = 'User Push Token'
        verbose_name_plural = 'User Push Tokens'
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.user.username} — {self.platform} ({self.device_label or 'unnamed'})"
