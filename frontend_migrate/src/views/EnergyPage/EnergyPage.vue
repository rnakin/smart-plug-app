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
import { ref, onMounted } from 'vue'
import Sidebar from '../../components/Sidebar/Sidebar.vue'

const houseName = ref('บ้านสุขสบาย')
const period = ref('daily')

const kpi = ref({
  today: 12.45,
  month: 285.32,
  power: 3240
})

const chartData = ref([30, 45, 35, 50, 40, 60, 55, 45, 70, 65, 50, 40, 35, 45])

const topDevices = ref([
  { name: 'เตาไฟฟ้า', kwh: 45.23, percentage: 100 },
  { name: 'แอร์', kwh: 38.12, percentage: 84 },
  { name: 'เครื่องซักผ้า', kwh: 25.67, percentage: 57 },
  { name: 'ตู้เย็น', kwh: 18.45, percentage: 41 },
  { name: 'ทีวี', kwh: 12.34, percentage: 27 }
])

const plugBreakdown = ref([
  { id: 1, name: 'เตาไฟฟ้า', location: 'ครัว', avgPower: 850, peakPower: 1240, kwh: 45.234, percentage: 100 },
  { id: 2, name: 'แอร์', location: 'ห้องนอน', avgPower: 720, peakPower: 900, kwh: 38.123, percentage: 84 },
  { id: 3, name: 'เครื่องซักผ้า', location: 'ห้องซัก', avgPower: 650, peakPower: 850, kwh: 25.672, percentage: 57 },
  { id: 4, name: 'ตู้เย็น', location: 'ครัว', avgPower: 120, peakPower: 150, kwh: 18.452, percentage: 41 }
])

const exportData = (format) => {
  // TODO: GET /api/houses/{house.id}/energy/export/?format={format}
  console.log(`Exporting energy data as ${format}...`)
}

onMounted(() => {
  // TODO: Load energy data
  // TODO: GET /api/houses/{house.id}/energy/dashboard/
  // TODO: GET /api/houses/{house.id}/energy/summary/
  // TODO: GET /api/houses/{house.id}/energy/by-plug/
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
