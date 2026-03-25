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
import { ref, computed, onMounted, watch } from 'vue'
import Sidebar from '../../components/Sidebar/Sidebar.vue'
import AlertPill from '../../components/AlertPill/AlertPill.vue'
import HouseTab from '../../components/HouseTab/HouseTab.vue'
import QuickStats from '../../components/QuickStats/QuickStats.vue'
import PlugCard from '../../components/PlugCard/PlugCard.vue'
import SummaryBar from '../../components/SummaryBar/SummaryBar.vue'
import AddHousePopup from '../../components/AddHousePopup/AddHousePopup.vue'
import AddPlugModal from '../../components/AddPlugModal/AddPlugModal.vue'
import { useAuth } from '../../composables/useAuth'
import { useHouses } from '../../composables/useHouses'
import { usePlugs } from '../../composables/usePlugs'
import { useEnergy } from '../../composables/useEnergy'
import { useAlerts } from '../../composables/useAlerts'

// Composables
const { user, fetchUser } = useAuth()
const { houses, fetchHouses, createHouse, isLoading: housesLoading } = useHouses()
const { plugs, fetchPlugs, togglePlug: togglePlugApi, createPlug, isLoading: plugsLoading } = usePlugs()
const { energySummary, fetchSummary } = useEnergy()
const { pendingEvents, fetchEvents, acknowledgeEvent, isLoading: alertsLoading } = useAlerts()

// User state
const username = computed(() => user.value?.username || 'User')
const liveStatus = ref('กำลังโหลด...')

// House state
const activeHouseId = ref(null)
const activeHouse = computed(() => houses.value.find(h => h.id === activeHouseId.value))
const roleLabel = computed(() => {
  const map = { owner: 'เจ้าของ', admin: 'ผู้ดูแล', member: 'สมาชิก', guest: 'แขก' }
  return map[activeHouse.value?.user_role] || activeHouse.value?.user_role || ''
})

// Plug state
const onlineCount = computed(() => plugs.value.filter(p => p.is_on).length)
const totalPower = computed(() => plugs.value.reduce((sum, p) => sum + (p.current_power_w || 0), 0))
const todayKwh = computed(() => energySummary.value?.today_kwh || 0)

// Alert state
const activeAlerts = computed(() => pendingEvents.value)
const alertsCount = computed(() => activeAlerts.value.length)

// Modal state
const showAddHousePopup = ref(false)
const showAddPlugModal = ref(false)

// Load data for active house
async function loadHouseData(houseId) {
  if (!houseId) return
  
  try {
    await Promise.all([
      fetchPlugs(houseId),
      fetchSummary(houseId),
      fetchEvents(houseId, { status: 'pending' })
    ])
    liveStatus.value = 'ทุกอย่างปกติดี ✓'
  } catch (err) {
    liveStatus.value = 'เกิดข้อผิดพลาดในการโหลดข้อมูล'
    console.error('Error loading house data:', err)
  }
}

// Watch for house changes
watch(activeHouseId, (newId) => {
  if (newId) {
    loadHouseData(newId)
  }
})

// Methods
const selectHouse = (house) => {
  activeHouseId.value = house.id
  liveStatus.value = `บ้าน ${house.name} ออนไลน์`
}

const togglePlug = async (plug) => {
  if (!activeHouseId.value) return
  
  try {
    await togglePlugApi(activeHouseId.value, plug.id, plug.is_on)
  } catch (err) {
    console.error('Error toggling plug:', err)
  }
}

const openPlugDetail = (plug) => {
  // TODO: Open plug detail drawer/modal
  console.log('Open plug detail:', plug)
}

const acknowledgeAlert = async (alertId) => {
  if (!activeHouseId.value) return
  
  try {
    await acknowledgeEvent(activeHouseId.value, alertId)
  } catch (err) {
    console.error('Error acknowledging alert:', err)
  }
}

const addHouse = async (houseData) => {
  try {
    const newHouse = await createHouse(houseData)
    activeHouseId.value = newHouse.id
    showAddHousePopup.value = false
  } catch (err) {
    console.error('Error creating house:', err)
  }
}

const addPlug = async (plugData) => {
  if (!activeHouseId.value) return
  
  try {
    await createPlug(activeHouseId.value, plugData)
    showAddPlugModal.value = false
  } catch (err) {
    console.error('Error creating plug:', err)
  }
}

// Initialize on mount
onMounted(async () => {
  try {
    // Fetch user info
    await fetchUser()
    
    // Fetch houses
    await fetchHouses()
    
    // Set first house as active
    if (houses.value.length > 0) {
      activeHouseId.value = houses.value[0].id
    } else {
      liveStatus.value = 'ยังไม่มีบ้าน — เพิ่มบ้านเพื่อเริ่มต้น'
    }
  } catch (err) {
    console.error('Error initializing:', err)
    liveStatus.value = 'เกิดข้อผิดพลาดในการโหลดข้อมูล'
  }
})
</script>

<style scoped>
@import './HomePage.css';
</style>
