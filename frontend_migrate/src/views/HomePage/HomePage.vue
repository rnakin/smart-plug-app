<template>
  <div class="dashboard-layout">
    <Sidebar />
    <div class="main-content">
      <!-- Top header -->
      <div class="home-header">
        <div>
          <div class="greeting">สวัสดี, <span id="username">{{ username }}</span></div>
          <div class="greeting-sub">
            <div class="live-dot-home"></div>
            <span id="live-status">{{ liveStatus }}</span>
          </div>
        </div>

        <!-- Alert pills -->
        <div class="alerts-zone">
          <AlertPill 
            v-for="alert in activeAlerts" 
            :key="alert.id"
            :alert="alert"
            @acknowledge="acknowledgeAlert"
          />
        </div>
      </div>

      <!-- House tabs row -->
      <div class="house-row">
        <HouseTab 
          v-for="house in houses" 
          :key="house.id"
          :house="house"
          :active="house.id === activeHouseId"
          @select="selectHouse"
        />
        <button class="htab-add" @click="showAddHousePopup = true">
          <svg width="11" height="11" fill="none" viewBox="0 0 24 24">
            <path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
          เพิ่มบ้าน
        </button>
      </div>

      <!-- Digital twin section -->
      <div class="twin-section">
        <QuickStats 
          :online="onlineCount"
          :alerts="alertsCount"
          :power="totalPower"
        />

        <div class="twin-toolbar">
          <div class="tb-left">
            <button class="tbtn primary" @click="showAddPlugModal = true">
              <svg width="12" height="12" fill="none" viewBox="0 0 24 24">
                <path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
              </svg>
              เพิ่มปลั๊ก
            </button>
          </div>
          <span class="role-badge">{{ roleLabel }}</span>
        </div>

        <!-- Plug grid -->
        <div class="twin-canvas">
          <div v-if="plugs.length === 0" class="plug-empty">
            <div style="font-size: 40px; margin-bottom: 12px;">🔌</div>
            <p style="font-size: 14px;">ยังไม่มีปลั๊กในบ้านนี้</p>
            <small>คลิก "เพิ่มปลั๊ก" เพื่อลงทะเบียนปลั๊กอัจฉริยะ</small>
          </div>
          <PlugCard 
            v-for="plug in plugs" 
            :key="plug.id"
            :plug="plug"
            @toggle="togglePlug"
            @click="openPlugDetail(plug)"
          />
        </div>
      </div>

      <!-- Summary bar -->
      <SummaryBar 
        :plug-count="plugs.length"
        :total-power="totalPower"
        :today-kwh="todayKwh"
        :alert-count="alertsCount"
      />

      <!-- Add House Popup -->
      <AddHousePopup 
        v-if="showAddHousePopup"
        @close="showAddHousePopup = false"
        @add="addHouse"
      />

      <!-- Add Plug Modal -->
      <AddPlugModal 
        v-if="showAddPlugModal"
        @close="showAddPlugModal = false"
        @add="addPlug"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Sidebar from '../../components/Sidebar/Sidebar.vue'
import AlertPill from '../../components/AlertPill/AlertPill.vue'
import HouseTab from '../../components/HouseTab/HouseTab.vue'
import QuickStats from '../../components/QuickStats/QuickStats.vue'
import PlugCard from '../../components/PlugCard/PlugCard.vue'
import SummaryBar from '../../components/SummaryBar/SummaryBar.vue'
import AddHousePopup from '../../components/AddHousePopup/AddHousePopup.vue'
import AddPlugModal from '../../components/AddPlugModal/AddPlugModal.vue'

// User state
const username = ref('User')
const liveStatus = ref('กำลังโหลด...')

// House state
const houses = ref([
  { id: 1, house_name: 'บ้านสุขสบาย', emoji: '🏠', role: 'owner' },
  { id: 2, house_name: 'ออฟฟิศ', emoji: '🏢', role: 'admin' }
])
const activeHouseId = ref(1)
const activeHouse = computed(() => houses.value.find(h => h.id === activeHouseId.value))
const roleLabel = computed(() => {
  const map = { owner: 'เจ้าของ', admin: 'ผู้ดูแล', member: 'สมาชิก', guest: 'แขก' }
  return map[activeHouse.value?.role] || activeHouse.value?.role || ''
})

// Plug state
const plugs = ref([
  { id: 1, name: 'เตาไฟฟ้า', location: 'ครัว', plug_code: 'KW-001', is_on: true, online_status: 'online', power: 1240 },
  { id: 2, name: 'ตู้เย็น', location: 'ครัว', plug_code: 'KW-002', is_on: true, online_status: 'online', power: 150 },
  { id: 3, name: 'เตารีด', location: 'ห้องนอน', plug_code: 'KW-003', is_on: false, online_status: 'offline', power: 0 },
  { id: 4, name: 'แอร์', location: 'ห้องนอน', plug_code: 'KW-004', is_on: true, online_status: 'online', power: 900 },
])

const onlineCount = computed(() => plugs.value.filter(p => p.is_on).length)
const totalPower = computed(() => plugs.value.reduce((sum, p) => sum + (p.power || 0), 0))
const todayKwh = ref(12.4)

// Alert state
const activeAlerts = ref([
  { id: 1, title: 'เตารีดในห้องนอนเปิดทิ้งไว้เกิน 30 นาที', severity: 'warn' },
  { id: 2, title: 'ตรวจพบพลังงานผิดปกติ — ครัว A1 สูงกว่าปกติ 40%', severity: 'danger' }
])
const alertsCount = computed(() => activeAlerts.value.length)

// Modal state
const showAddHousePopup = ref(false)
const showAddPlugModal = ref(false)

// Methods
const selectHouse = (house) => {
  activeHouseId.value = house.id
  // TODO: Load plugs for selected house
  // TODO: GET /api/houses/{house.id}/plugs/
  liveStatus.value = `บ้าน ${house.house_name} ออนไลน์`
}

const togglePlug = async (plug) => {
  // TODO: POST /api/houses/{house.id}/plugs/{plug.id}/control/
  plug.is_on = !plug.is_on
  plug.power = plug.is_on ? Math.floor(Math.random() * 1000) + 100 : 0
}

const openPlugDetail = (plug) => {
  // TODO: Open plug detail drawer/modal
  console.log('Open plug detail:', plug)
}

const acknowledgeAlert = (alertId) => {
  // TODO: POST /api/houses/{house.id}/alerts/events/{alertId}/action/
  activeAlerts.value = activeAlerts.value.filter(a => a.id !== alertId)
}

const addHouse = (houseData) => {
  // TODO: POST /api/houses/
  const newHouse = {
    id: houses.value.length + 1,
    ...houseData,
    role: 'owner'
  }
  houses.value.push(newHouse)
  showAddHousePopup.value = false
}

const addPlug = (plugData) => {
  // TODO: POST /api/houses/{house.id}/plugs/
  const newPlug = {
    id: plugs.value.length + 1,
    ...plugData,
    is_on: false,
    online_status: 'offline',
    power: 0
  }
  plugs.value.push(newPlug)
  showAddPlugModal.value = false
}

// TODO: Load houses on mount
// TODO: GET /api/houses/
onMounted(() => {
  // Set initial status
  if (houses.value.length > 0) {
    liveStatus.value = 'ทุกอย่างปกติดี ✓'
  } else {
    liveStatus.value = 'ยังไม่มีบ้าน — เพิ่มบ้านเพื่อเริ่มต้น'
  }
  
  // TODO: Fetch current user
  // TODO: GET /auth/me/
})
</script>

<style scoped>
@import './HomePage.css';
</style>
