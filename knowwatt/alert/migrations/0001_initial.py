from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('device', '0001_initial'),
        ('house', '0003_house_emoji_alter_housemember_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('trigger', models.CharField(choices=[
                    ('power_above', 'Power above threshold (W)'),
                    ('power_below', 'Power below threshold (W)'),
                    ('duration_above', 'Device on longer than N minutes'),
                    ('device_plugged_in', 'Device plugged in (NFC detected)'),
                    ('device_unplugged', 'Device unplugged / session ended'),
                    ('offline', 'Plug went offline'),
                ], max_length=30)),
                ('threshold_value', models.FloatField(blank=True, null=True)),
                ('action', models.CharField(choices=[('notify', 'Notify only'), ('auto_off', 'Auto power-off plug')], default='notify', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('house', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alert_rules', to='house.house')),
                ('plug', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='alert_rules', to='device.smartplug')),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='alert_rules', to='device.electricaldevice')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_alert_rules', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Alert Rule',
                'verbose_name_plural': 'Alert Rules',
                'db_table': 'alert_rule',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AlertEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('trigger_value', models.FloatField(blank=True, null=True)),
                ('status', models.CharField(choices=[
                    ('pending', 'Pending — awaiting user response'),
                    ('acknowledged', 'Acknowledged'),
                    ('snoozed', 'Snoozed — remind later'),
                    ('dismissed', 'Dismissed'),
                    ('auto_resolved', 'Auto-resolved by system'),
                ], default='pending', max_length=20)),
                ('triggered_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('snooze_until', models.DateTimeField(blank=True, null=True)),
                ('push_sent', models.BooleanField(default=False)),
                ('push_sent_at', models.DateTimeField(blank=True, null=True)),
                ('rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='alert.alertrule')),
                ('house', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alert_events', to='house.house')),
                ('plug', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='alert_events', to='device.smartplug')),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='alert_events', to='device.electricaldevice')),
            ],
            options={
                'verbose_name': 'Alert Event',
                'verbose_name_plural': 'Alert Events',
                'db_table': 'alert_event',
                'ordering': ['-triggered_at'],
            },
        ),
        migrations.AddIndex(
            model_name='alertevent',
            index=models.Index(fields=['house', 'status', 'triggered_at'], name='alert_event_house_status_idx'),
        ),
        migrations.CreateModel(
            name='UserPushToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token', models.TextField(unique=True)),
                ('platform', models.CharField(choices=[('fcm', 'Firebase Cloud Messaging (Android/Web)'), ('apns', 'Apple Push Notification Service (iOS)')], default='fcm', max_length=10)),
                ('device_label', models.CharField(blank=True, default='', max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='push_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Push Token',
                'verbose_name_plural': 'User Push Tokens',
                'db_table': 'user_push_token',
                'ordering': ['-registered_at'],
            },
        ),
    ]
