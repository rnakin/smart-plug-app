from django.contrib import admin
from .models import AlertRule, AlertEvent, UserPushToken


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ('trigger', 'action', 'house', 'plug', 'device', 'is_active', 'created_at')
    list_filter = ('trigger', 'action', 'is_active')
    search_fields = ('house__house_name',)


@admin.register(AlertEvent)
class AlertEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'house', 'plug', 'device', 'triggered_at')
    list_filter = ('status',)
    search_fields = ('title', 'message')
    ordering = ('-triggered_at',)


@admin.register(UserPushToken)
class UserPushTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform', 'device_label', 'is_active', 'registered_at')
    list_filter = ('platform', 'is_active')
