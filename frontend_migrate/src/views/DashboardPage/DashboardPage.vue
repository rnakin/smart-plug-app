<template>
  <div class="dashboard-layout">
    <Sidebar />
    <div class="center-panel">
      <div class="top-bar">
        <div>
          <div class="top-bar-title">📊 Dashboard</div>
          <div class="top-bar-sub">{{ houseName }}</div>
        </div>
        <div class="top-bar-actions">
          <button class="btn btn-ghost" @click="refresh">
            <svg width="14" height="14" fill="none" viewBox="0 0 24 24">
              <path d="M23 4v6h-6M1 20v-6h6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            รีเฟรช
          </button>
        </div>
      </div>

      <div class="dashboard-content">
        <!-- KPI cards -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-label">ปลั๊กทั้งหมด</div>
            <div class="stat-value">{{ totalPlugs }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">เปิดอยู่</div>
            <div class="stat-value" style="color:var(--accent)">{{ onPlugs }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">กำลังไฟรวม</div>
            <div class="stat-value">{{ totalPower.toLocaleString() }}<span class="stat-unit">W</span></div>
          </div>
          <div class="stat-card">
            <div class="stat-label">วันนี้</div>
            <div class="stat-value">{{ todayKwh }}<span class="stat-unit">kWh</span></div>
          </div>
        </div>

        <!-- Plug list -->
        <div class="plug-list">
          <PlugCard 
            v-for="plug in plugs" 
            :key="plug.id"
            :plug="plug"
            @toggle="togglePlug"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Sidebar from '../../components/Sidebar/Sidebar.vue'
import PlugCard from '../../components/PlugCard/PlugCard.vue'

const houseName = ref('บ้านสุขสบาย')
const totalPlugs = ref(7)
const onPlugs = ref(4)
const totalPower = ref(3240)
const todayKwh = ref(12.4)

const plugs = ref([
  { id: 1, name: 'เตาไฟฟ้า', location: 'ครัว', plug_code: 'KW-001', is_on: true, online_status: 'online', power: 1240 },
  { id: 2, name: 'ตู้เย็น', location: 'ครัว', plug_code: 'KW-002', is_on: true, online_status: 'online', power: 150 },
  { id: 3, name: 'เตารีด', location: 'ห้องนอน', plug_code: 'KW-003', is_on: false, online_status: 'offline', power: 0 },
  { id: 4, name: 'แอร์', location: 'ห้องนอน', plug_code: 'KW-004', is_on: true, online_status: 'online', power: 900 },
  { id: 5, name: 'ทีวี', location: 'ห้องนั่งเล่น', plug_code: 'KW-005', is_on: true, online_status: 'online', power: 120 },
  { id: 6, name: 'พัดลม', location: 'ห้องนั่งเล่น', plug_code: 'KW-006', is_on: true, online_status: 'online', power: 65 },
  { id: 7, name: 'เครื่องซักผ้า', location: 'ห้องซัก', plug_code: 'KW-007', is_on: true, online_status: 'online', power: 850 },
])

const togglePlug = (plug) => {
  // TODO: POST /api/houses/{house.id}/plugs/{plug.id}/control/
  plug.is_on = !plug.is_on
  plug.power = plug.is_on ? Math.floor(Math.random() * 1000) + 100 : 0
  onPlugs.value = plugs.value.filter(p => p.is_on).length
  totalPower.value = plugs.value.reduce((sum, p) => sum + (p.power || 0), 0)
}

const refresh = () => {
  // TODO: GET /api/houses/{house.id}/plugs/
  console.log('Refreshing dashboard data...')
}

onMounted(() => {
  // TODO: Load dashboard data
  // TODO: GET /api/houses/{house.id}/energy/dashboard/
})
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg);
}

.plug-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
  margin-top: 20px;
}
</style>
