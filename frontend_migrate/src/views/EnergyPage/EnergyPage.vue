<template>
  <div class="dashboard-layout">
    <Sidebar />
    <div class="center-panel">
      <div class="top-bar">
        <div>
          <div class="top-bar-title">⚡ การใช้พลังงาน</div>
          <div class="top-bar-sub">{{ houseName }}</div>
        </div>
        <div class="top-bar-actions">
          <select v-model="period" class="period-select">
            <option value="daily">รายวัน</option>
            <option value="weekly">รายสัปดาห์</option>
            <option value="monthly">รายเดือน</option>
          </select>
          <button class="btn btn-ghost" @click="exportData('csv')">⬇ CSV</button>
          <button class="btn btn-ghost" @click="exportData('json')">⬇ JSON</button>
        </div>
      </div>

      <div class="dashboard-content">
        <!-- KPI cards -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">วันนี้</div>
            <div class="stat-value">{{ kpi.today }}<span class="stat-unit">kWh</span></div>
          </div>
          <div class="stat-card">
            <div class="stat-label">เดือนนี้</div>
            <div class="stat-value">{{ kpi.month }}<span class="stat-unit">kWh</span></div>
          </div>
          <div class="stat-card">
            <div class="stat-label">กำลังไฟปัจจุบัน</div>
            <div class="stat-value">{{ kpi.power }}<span class="stat-unit">W</span></div>
          </div>
        </div>

        <div class="content-grid">
          <!-- Chart -->
          <div class="card">
            <div class="card-header">
              <div class="card-title">กราฟการใช้พลังงาน</div>
            </div>
            <div class="chart-container">
              <!-- TODO: Add Chart.js integration -->
              <div class="chart-placeholder">
                <div v-for="(bar, i) in chartData" :key="i" class="chart-bar" :style="{ height: bar + '%' }"></div>
              </div>
            </div>
          </div>

          <!-- Top devices -->
          <div class="card">
            <div class="card-header">
              <div class="card-title">อุปกรณ์ใช้ไฟสูงสุด</div>
            </div>
            <div class="device-list">
              <div v-for="device in topDevices" :key="device.name" class="device-item">
                <div class="device-info">
                  <div class="device-name">{{ device.name }}</div>
                  <div class="device-bar">
                    <div class="device-bar-fill" :style="{ width: device.percentage + '%' }"></div>
                  </div>
                </div>
                <div class="device-value">{{ device.kwh }} kWh</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Per-plug breakdown -->
        <div class="card" style="margin-top: 16px;">
          <div class="card-header">
            <div class="card-title">การใช้พลังงานแยกตามปลั๊ก</div>
          </div>
          <div class="plug-list">
            <div v-for="plug in plugBreakdown" :key="plug.id" class="plug-item">
              <div class="plug-icon">🔌</div>
              <div class="plug-info">
                <div class="plug-name">{{ plug.name }}</div>
                <div class="plug-meta">{{ plug.location }} · เฉลี่ย {{ plug.avgPower }}W · สูงสุด {{ plug.peakPower }}W</div>
                <div class="plug-bar">
                  <div class="plug-bar-fill" :style="{ width: plug.percentage + '%' }"></div>
                </div>
              </div>
              <div class="plug-value">
                <div class="plug-kwh">{{ plug.kwh }}</div>
                <div class="plug-unit">kWh</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import Sidebar from '../../components/Sidebar/Sidebar.vue'
import { useHouses } from '../../composables/useHouses'
import { useEnergy } from '../../composables/useEnergy'

// Composables
const { houses, fetchHouses, currentHouse, setCurrentHouse } = useHouses()
const { 
  energySummary, 
  dashboardData, 
  plugEnergy, 
  deviceEnergy,
  fetchSummary, 
  fetchDashboard, 
  fetchByPlug, 
  fetchByDevice,
  exportData: exportEnergyData 
} = useEnergy()

// State
const period = ref('daily')
const activeHouseId = ref(null)

// Computed
const houseName = computed(() => currentHouse.value?.name || 'เลือกบ้าน')

const kpi = computed(() => ({
  today: energySummary.value?.today_kwh?.toFixed(2) || '0.00',
  month: energySummary.value?.month_kwh?.toFixed(2) || '0.00',
  power: dashboardData.value?.current_power_w || 0
}))

const chartData = computed(() => {
  // Generate chart data from readings or use placeholder
  const readings = dashboardData.value?.hourly_readings || []
  if (readings.length > 0) {
    const max = Math.max(...readings.map(r => r.power_w || 0))
    return readings.map(r => max > 0 ? ((r.power_w || 0) / max) * 100 : 0)
  }
  return [30, 45, 35, 50, 40, 60, 55, 45, 70, 65, 50, 40, 35, 45]
})

const topDevices = computed(() => {
  if (!deviceEnergy.value || deviceEnergy.value.length === 0) {
    return []
  }
  const maxKwh = Math.max(...deviceEnergy.value.map(d => d.total_kwh || 0))
  return deviceEnergy.value.slice(0, 5).map(d => ({
    name: d.device_name || d.name,
    kwh: (d.total_kwh || 0).toFixed(2),
    percentage: maxKwh > 0 ? ((d.total_kwh || 0) / maxKwh) * 100 : 0
  }))
})

const plugBreakdown = computed(() => {
  if (!plugEnergy.value || plugEnergy.value.length === 0) {
    return []
  }
  const maxKwh = Math.max(...plugEnergy.value.map(p => p.total_kwh || 0))
  return plugEnergy.value.map(p => ({
    id: p.plug_id || p.id,
    name: p.plug_name || p.name,
    location: p.location || '-',
    avgPower: Math.round(p.avg_power_w || 0),
    peakPower: Math.round(p.peak_power_w || 0),
    kwh: (p.total_kwh || 0).toFixed(3),
    percentage: maxKwh > 0 ? ((p.total_kwh || 0) / maxKwh) * 100 : 0
  }))
})

// Methods
const exportData = async (format) => {
  if (!activeHouseId.value) return
  
  try {
    const blob = await exportEnergyData(activeHouseId.value, { format })
    
    // Create download link
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `energy-data.${format}`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (err) {
    console.error('Error exporting data:', err)
  }
}

const loadEnergyData = async () => {
  if (!activeHouseId.value) return
  
  try {
    const periodMap = { daily: 'day', weekly: 'week', monthly: 'month' }
    await Promise.all([
      fetchSummary(activeHouseId.value, { period: periodMap[period.value] }),
      fetchDashboard(activeHouseId.value),
      fetchByPlug(activeHouseId.value),
      fetchByDevice(activeHouseId.value)
    ])
  } catch (err) {
    console.error('Error loading energy data:', err)
  }
}

// Watch for period changes
watch(period, () => {
  loadEnergyData()
})

// Initialize on mount
onMounted(async () => {
  try {
    // Fetch houses
    await fetchHouses()
    
    // Get active house from localStorage or use first house
    const storedHouseId = localStorage.getItem('activeHouseId')
    if (storedHouseId) {
      activeHouseId.value = storedHouseId
      const house = houses.value.find(h => h.id === storedHouseId)
      if (house) setCurrentHouse(house)
    } else if (houses.value.length > 0) {
      activeHouseId.value = houses.value[0].id
      setCurrentHouse(houses.value[0])
    }
    
    // Load energy data
    if (activeHouseId.value) {
      await loadEnergyData()
    }
  } catch (err) {
    console.error('Error initializing energy page:', err)
  }
})
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg);
}

.period-select {
  padding: 7px 12px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 13px;
  font-family: 'DM Sans', sans-serif;
  outline: none;
  cursor: pointer;
}

.chart-container {
  padding: 16px;
  height: 260px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.chart-placeholder {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 100%;
  width: 100%;
  justify-content: space-around;
}

.chart-bar {
  width: 20px;
  background: var(--accent);
  border-radius: 4px 4px 0 0;
  opacity: 0.8;
}

.device-list {
  padding: 8px 0;
}

.device-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
}

.device-info {
  flex: 1;
}

.device-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 4px;
}

.device-bar {
  height: 4px;
  background: var(--surface3);
  border-radius: 2px;
  overflow: hidden;
}

.device-bar-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
}

.device-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
  font-family: 'DM Mono', monospace;
}

.plug-list {
  padding: 8px 0;
}

.plug-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.plug-icon {
  font-size: 18px;
}

.plug-info {
  flex: 1;
}

.plug-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
}

.plug-meta {
  font-size: 11px;
  color: var(--text3);
  margin-bottom: 5px;
}

.plug-bar {
  height: 4px;
  background: var(--surface3);
  border-radius: 2px;
  overflow: hidden;
}

.plug-bar-fill {
  height: 100%;
  background: var(--accent2);
  border-radius: 2px;
}

.plug-value {
  text-align: right;
}

.plug-kwh {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent2);
  font-family: 'DM Mono', monospace;
}

.plug-unit {
  font-size: 10px;
  color: var(--text3);
}
</style>
