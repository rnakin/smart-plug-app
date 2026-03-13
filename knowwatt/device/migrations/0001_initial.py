from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('house', '0003_house_emoji_alter_housemember_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SmartPlug',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('plug_code', models.CharField(max_length=64, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('location', models.CharField(blank=True, default='', max_length=255)),
                ('is_on', models.BooleanField(default=False)),
                ('online_status', models.CharField(choices=[('online', 'Online'), ('offline', 'Offline')], default='offline', max_length=10)),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('house', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plugs', to='house.house')),
                ('registered_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='registered_plugs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Smart Plug',
                'verbose_name_plural': 'Smart Plugs',
                'db_table': 'smart_plug',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ElectricalDevice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('device_type', models.CharField(choices=[('appliance', 'Appliance'), ('entertainment', 'Entertainment'), ('lighting', 'Lighting'), ('hvac', 'HVAC'), ('kitchen', 'Kitchen'), ('office', 'Office'), ('other', 'Other')], default='other', max_length=30)),
                ('rated_power_watts', models.FloatField(help_text='Rated power in watts from spec')),
                ('risk_level', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='low', max_length=10)),
                ('auto_cutoff_minutes', models.IntegerField(blank=True, help_text='Auto power-off after this many minutes of continuous use (null = disabled)', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('house', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devices', to='house.house')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_devices', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Electrical Device',
                'verbose_name_plural': 'Electrical Devices',
                'db_table': 'electrical_device',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='NFCTag',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tag_uid', models.CharField(help_text='Unique NFC tag UID', max_length=128, unique=True)),
                ('label', models.CharField(blank=True, default='', help_text='Optional label for this tag', max_length=100)),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('device', models.ForeignKey(blank=True, help_text='Paired electrical device (null = unregistered tag)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='nfc_tags', to='device.electricaldevice')),
                ('registered_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='registered_nfc_tags', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'NFC Tag',
                'verbose_name_plural': 'NFC Tags',
                'db_table': 'nfc_tag',
                'ordering': ['-registered_at'],
            },
        ),
        migrations.CreateModel(
            name='PlugSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('plug', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='device.smartplug')),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sessions', to='device.electricaldevice')),
                ('nfc_tag', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sessions', to='device.nfctag')),
            ],
            options={
                'verbose_name': 'Plug Session',
                'verbose_name_plural': 'Plug Sessions',
                'db_table': 'plug_session',
                'ordering': ['-started_at'],
            },
        ),
    ]
