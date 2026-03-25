<template>
  <div class="dashboard-layout">
    <Sidebar />
    <div class="center-panel">
      <div class="top-bar">
        <div>
          <div class="top-bar-title">🔔 การแจ้งเตือน</div>
          <div class="top-bar-sub">{{ houseName }}</div>
        </div>
        <div class="top-bar-actions">
          <select v-model="statusFilter" class="status-select">
            <option value="pending">รอดำเนินการ</option>
            <option value="acknowledged">รับทราบแล้ว</option>
            <option value="snoozed">เลื่อนแจ้งเตือน</option>
            <option value="dismissed">ยกเลิกแล้ว</option>
            <option value="all">ทั้งหมด</option>
          </select>
          <button class="btn btn-ghost" @click="refresh">รีเฟรช</button>
        </div>
      </div>

      <div class="dashboard-content">
        <div v-if="alerts.length === 0" class="empty-state">
          ไม่มีการแจ้งเตือน
        </div>
        <div v-else class="alerts-list">
          <div 
            v-for="alert in alerts" 
            :key="alert.id" 
            class="alert-item"
            :class="alert.severity"
          >
            <div class="alert-icon">{{ alert.icon }}</div>
            <div class="alert-content">
              <div class="alert-title">{{ alert.title }}</div>
              <div class="alert-meta">{{ alert.plug }} · {{ alert.time }}</div>
            </div>
            <div class="alert-actions">
              <button v-if="alert.status === 'pending'" class="btn-ack" @click="acknowledge(alert.id)">
                รับทราบ
              </button>
              <span v-else class="alert-status">{{ alert.statusText }}</span>
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
import { useAlerts } from '../../composables/useAlerts'

// Composables
const { houses, fetchHouses, currentHouse, setCurrentHouse } = useHouses()
const { 
  alertEvents, 
  fetchAlertEvents, 
  acknowledgeAlert,
  loading,
  error 
} = useAlerts()

// State
const statusFilter = ref('pending')
const activeHouseId = ref(null)

// Computed
const houseName = computed(() => currentHouse.value?.name || 'เลือกบ้าน')

const alerts = computed(() => {
  if (!alertEvents.value || alertEvents.value.length === 0) {
    return []
  }
  
  return alertEvents.value.map(event => {
    // Determine severity based on alert rule type or threshold
    const severity = event.severity || (event.alert_rule?.severity === 'critical' ? 'danger' : 'warn')
    
    // Get icon based on alert type
    const icon = severity === 'danger' ? '🔴' : '⚠️'
    
    // Format time
    const timeAgo = formatTimeAgo(event.triggered_at || event.created_at)
    
    // Get status text
    const statusTextMap = {
      pending: 'รอดำเนินการ',
      acknowledged: 'รับทราบแล้ว',
      snoozed: 'เลื่อนแจ้งเตือน',
      dismissed: 'ยกเลิกแล้ว'
    }
    
    return {
      id: event.id,
      title: event.message || event.alert_rule?.name || 'การแจ้งเตือน',
      plug: event.plug?.name || event.device_name || '-',
      time: timeAgo,
      severity,
      status: event.status || 'pending',
      statusText: statusTextMap[event.status] || 'รอดำเนินการ',
      icon
    }
  })
})

// Helper to format time ago
const formatTimeAgo = (dateString) => {
  if (!dateString) return '-'
  
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) return 'เมื่อสักครู่'
  if (diffMins < 60) return `${diffMins} นาทีที่แล้ว`
  if (diffHours < 24) return `${diffHours} ชั่วโมงที่แล้ว`
  return `${diffDays} วันที่แล้ว`
}

// Methods
const acknowledge = async (alertId) => {
  if (!activeHouseId.value) return
  
  try {
    await acknowledgeAlert(activeHouseId.value, alertId, 'acknowledge')
    // Refresh the alerts list
    await fetchAlertEvents(activeHouseId.value, { status: statusFilter.value === 'all' ? undefined : statusFilter.value })
  } catch (err) {
    console.error('Error acknowledging alert:', err)
  }
}

const refresh = async () => {
  if (!activeHouseId.value) return
  
  try {
    await fetchAlertEvents(activeHouseId.value, { 
      status: statusFilter.value === 'all' ? undefined : statusFilter.value 
    })
  } catch (err) {
    console.error('Error refreshing alerts:', err)
  }
}

// Watch for filter changes
watch(statusFilter, () => {
  refresh()
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
    
    // Load alerts
    if (activeHouseId.value) {
      await fetchAlertEvents(activeHouseId.value, { 
        status: statusFilter.value === 'all' ? undefined : statusFilter.value 
      })
    }
  } catch (err) {
    console.error('Error initializing alerts page:', err)
  }
})
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg);
}

.status-select {
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

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text3);
  font-size: 14px;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
}

.alert-item.warn {
  border-left: 3px solid var(--warn);
}

.alert-item.danger {
  border-left: 3px solid var(--danger);
}

.alert-icon {
  font-size: 20px;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 4px;
}

.alert-meta {
  font-size: 12px;
  color: var(--text2);
}

.alert-actions {
  display: flex;
  align-items: center;
}

.btn-ack {
  padding: 6px 12px;
  background: var(--accent-dim);
  color: var(--accent);
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
}

.btn-ack:hover {
  filter: brightness(1.1);
}

.alert-status {
  font-size: 12px;
  color: var(--text2);
}
</style>
