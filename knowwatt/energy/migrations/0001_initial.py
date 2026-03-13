from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('device', '0001_initial'),
        ('house', '0003_house_emoji_alter_housemember_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnergyReading',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('voltage_v', models.FloatField(help_text='Voltage in Volts')),
                ('current_a', models.FloatField(help_text='Current in Amperes')),
                ('power_w', models.FloatField(help_text='Active power in Watts')),
                ('energy_kwh', models.FloatField(default=0.0, help_text='Cumulative energy in kWh (from plug counter)')),
                ('recorded_at', models.DateTimeField(db_index=True, help_text='Timestamp of the reading')),
                ('plug', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='energy_readings', to='device.smartplug')),
                ('session', models.ForeignKey(blank=True, help_text='Active plug session when this reading was taken', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='energy_readings', to='device.plugsession')),
                ('device', models.ForeignKey(blank=True, help_text='Device plugged in at time of reading (denormalized for fast queries)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='energy_readings', to='device.electricaldevice')),
            ],
            options={
                'verbose_name': 'Energy Reading',
                'verbose_name_plural': 'Energy Readings',
                'db_table': 'energy_reading',
                'ordering': ['-recorded_at'],
            },
        ),
        migrations.AddIndex(
            model_name='energyreading',
            index=models.Index(fields=['plug', 'recorded_at'], name='energy_read_plug_id_idx'),
        ),
        migrations.AddIndex(
            model_name='energyreading',
            index=models.Index(fields=['device', 'recorded_at'], name='energy_read_device_id_idx'),
        ),
        migrations.CreateModel(
            name='DailyEnergySummary',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField(db_index=True)),
                ('total_kwh', models.FloatField(default=0.0)),
                ('avg_power_w', models.FloatField(default=0.0)),
                ('peak_power_w', models.FloatField(default=0.0)),
                ('reading_count', models.IntegerField(default=0)),
                ('plug', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_summaries', to='device.smartplug')),
                ('house', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_summaries', to='house.house')),
            ],
            options={
                'verbose_name': 'Daily Energy Summary',
                'verbose_name_plural': 'Daily Energy Summaries',
                'db_table': 'daily_energy_summary',
                'ordering': ['-date'],
                'unique_together': {('plug', 'date')},
            },
        ),
    ]
