from django.db import models
import uuid
from device.models import SmartPlug, ElectricalDevice, PlugSession
from house.models import House


class EnergyReading(models.Model):
    """
    Time-series energy reading from a smart plug.
    Recorded periodically (e.g. every 30s–1min) by the plug firmware.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plug = models.ForeignKey(SmartPlug, on_delete=models.CASCADE, related_name='energy_readings')
    session = models.ForeignKey(
        PlugSession,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='energy_readings',
        help_text='Active plug session when this reading was taken'
    )
    device = models.ForeignKey(
        ElectricalDevice,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='energy_readings',
        help_text='Device plugged in at time of reading (denormalized for fast queries)'
    )

    # Electrical measurements
    voltage_v = models.FloatField(help_text='Voltage in Volts')
    current_a = models.FloatField(help_text='Current in Amperes')
    power_w = models.FloatField(help_text='Active power in Watts')
    energy_kwh = models.FloatField(default=0.0, help_text='Cumulative energy in kWh (from plug counter)')

    recorded_at = models.DateTimeField(db_index=True, help_text='Timestamp of the reading')

    class Meta:
        db_table = 'energy_reading'
        verbose_name = 'Energy Reading'
        verbose_name_plural = 'Energy Readings'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['plug', 'recorded_at']),
            models.Index(fields=['device', 'recorded_at']),
        ]

    def __str__(self):
        return f"{self.plug.name} @ {self.recorded_at} — {self.power_w}W"


class DailyEnergySummary(models.Model):
    """
    Pre-aggregated daily energy summary per plug (for fast reporting).
    Can be computed by a background task or on-demand.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plug = models.ForeignKey(SmartPlug, on_delete=models.CASCADE, related_name='daily_summaries')
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='daily_summaries')
    date = models.DateField(db_index=True)

    total_kwh = models.FloatField(default=0.0)
    avg_power_w = models.FloatField(default=0.0)
    peak_power_w = models.FloatField(default=0.0)
    reading_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'daily_energy_summary'
        verbose_name = 'Daily Energy Summary'
        verbose_name_plural = 'Daily Energy Summaries'
        unique_together = ['plug', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.plug.name} — {self.date} — {self.total_kwh:.3f} kWh"
