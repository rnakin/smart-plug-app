from django.contrib import admin
from .models import EnergyReading, DailyEnergySummary


@admin.register(EnergyReading)
class EnergyReadingAdmin(admin.ModelAdmin):
    list_display = ('plug', 'device', 'power_w', 'voltage_v', 'current_a', 'energy_kwh', 'recorded_at')
    list_filter = ('plug__house',)
    search_fields = ('plug__name', 'device__name')
    ordering = ('-recorded_at',)


@admin.register(DailyEnergySummary)
class DailyEnergySummaryAdmin(admin.ModelAdmin):
    list_display = ('plug', 'date', 'total_kwh', 'avg_power_w', 'peak_power_w', 'reading_count')
    list_filter = ('house',)
    ordering = ('-date',)
