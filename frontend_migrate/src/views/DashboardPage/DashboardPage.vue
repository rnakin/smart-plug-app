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
import { ref, computed, onMounted } from 'vue'
import Sidebar from '../../components/Sidebar/Sidebar.vue'
import PlugCard from '../../components/PlugCard/PlugCard.vue'
import { useHouses } from '../../composables/useHouses'
import { usePlugs } from '../../composables/usePlugs'
import { useEnergy } from '../../composables/useEnergy'

// Composables
const { houses, fetchHouses, currentHouse, setCurrentHouse } = useHouses()
const { plugs, fetchPlugs, togglePlug: togglePlugApi } = usePlugs()
const { dashboardData, fetchDashboard } = useEnergy()

// Computed
const houseName = computed(() => currentHouse.value?.name || 'เลือกบ้าน')
const totalPlugs = computed(() => plugs.value.length)
const onPlugs = computed(() => plugs.value.filter(p => p.is_on).length)
const totalPower = computed(() => plugs.value.reduce((sum, p) => sum + (p.current_power_w || 0), 0))
const todayKwh = computed(() => dashboardData.value?.today_kwh?.toFixed(1) || '0.0')

// Get active house from localStorage or use first house
const activeHouseId = ref(null)

const togglePlug = async (plug) => {
  if (!activeHouseId.value) return
  
  try {
    await togglePlugApi(activeHouseId.value, plug.id, plug.is_on)
  } catch (err) {
    console.error('Error toggling plug:', err)
  }
}

const refresh = async () => {
  if (!activeHouseId.value) return
  
  try {
    await Promise.all([
      fetchPlugs(activeHouseId.value),
      fetchDashboard(activeHouseId.value)
    ])
  } catch (err) {
    console.error('Error refreshing dashboard:', err)
  }
}

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
    
    // Load dashboard data
    if (activeHouseId.value) {
      await Promise.all([
        fetchPlugs(activeHouseId.value),
        fetchDashboard(activeHouseId.value)
      ])
    }
  } catch (err) {
    console.error('Error loading dashboard:', err)
  }
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
