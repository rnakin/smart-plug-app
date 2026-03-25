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
import { ref, onMounted } from 'vue'
import Sidebar from '../../components/Sidebar/Sidebar.vue'

const houseName = ref('บ้านสุขสบาย')
const statusFilter = ref('pending')

const alerts = ref([
  { 
    id: 1, 
    title: 'เตารีดในห้องนอนเปิดทิ้งไว้เกิน 30 นาที', 
    plug: 'เตารีด (ห้องนอน)',
    time: '5 นาทีที่แล้ว',
    severity: 'warn',
    status: 'pending',
    statusText: 'รอดำเนินการ',
    icon: '⚠️'
  },
  { 
    id: 2, 
    title: 'ตรวจพบพลังงานผิดปกติ — ครัว A1 สูงกว่าปกติ 40%', 
    plug: 'เตาไฟฟ้า (ครัว)',
    time: '15 นาทีที่แล้ว',
    severity: 'danger',
    status: 'pending',
    statusText: 'รอดำเนินการ',
    icon: '🔴'
  },
  { 
    id: 3, 
    title: 'ปลั๊กออฟฟิศออฟไลน์', 
    plug: 'ปลั๊กคอมพิวเตอร์ (ออฟฟิศ)',
    time: '1 ชั่วโมงที่แล้ว',
    severity: 'warn',
    status: 'acknowledged',
    statusText: 'รับทราบแล้ว',
    icon: '⚠️'
  }
])

const acknowledge = (alertId) => {
  // TODO: POST /api/houses/{house.id}/alerts/events/{alertId}/action/
  const alert = alerts.value.find(a => a.id === alertId)
  if (alert) {
    alert.status = 'acknowledged'
    alert.statusText = 'รับทราบแล้ว'
  }
}

const refresh = () => {
  // TODO: GET /api/houses/{house.id}/alerts/events/?status={statusFilter}
  console.log('Refreshing alerts...')
}

onMounted(() => {
  // TODO: Load alerts from API
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
