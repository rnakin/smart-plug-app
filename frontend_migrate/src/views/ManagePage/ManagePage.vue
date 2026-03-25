<template>
  <div class="dashboard-layout">
    <Sidebar />
    <div class="center-panel">
      <div class="top-bar">
        <div>
          <div class="top-bar-title">🏠 จัดการบ้าน</div>
          <div class="top-bar-sub">{{ houseName }}</div>
        </div>
        <div class="top-bar-actions">
          <button class="btn btn-ghost" @click="refresh">รีเฟรช</button>
        </div>
      </div>

      <div class="dashboard-content">
        <div class="manage-grid">
          <!-- Members Card -->
          <div class="card">
            <div class="card-header">
              <div class="card-title">สมาชิกในบ้าน</div>
              <button class="btn btn-accent" @click="showAddMember = true">+ เพิ่มสมาชิก</button>
            </div>
            <div class="members-list">
              <div v-for="member in members" :key="member.id" class="member-item">
                <div class="member-avatar">{{ member.name[0] }}</div>
                <div class="member-info">
                  <div class="member-name">{{ member.name }}</div>
                  <div class="member-role">{{ member.role }}</div>
                </div>
                <button v-if="member.role !== 'เจ้าของ'" class="btn-remove" @click="removeMember(member.id)">
                  ลบ
                </button>
              </div>
            </div>
          </div>

          <!-- Settings Card -->
          <div class="card">
            <div class="card-header">
              <div class="card-title">ตั้งค่าบ้าน</div>
            </div>
            <div class="settings-form">
              <div class="field">
                <label>ชื่อบ้าน</label>
                <input v-model="houseSettings.name" type="text" class="modal-input">
              </div>
              <div class="field">
                <label>ที่อยู่</label>
                <input v-model="houseSettings.address" type="text" class="modal-input">
              </div>
              <button class="btn btn-accent" @click="saveSettings">บันทึก</button>
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
const showAddMember = ref(false)

const members = ref([
  { id: 1, name: 'คุณ', role: 'เจ้าของ' },
  { id: 2, name: 'ภรรยา', role: 'ผู้ดูแล' },
  { id: 3, name: 'ลูกชาย', role: 'สมาชิก' }
])

const houseSettings = ref({
  name: 'บ้านสุขสบาย',
  address: '123 ถนนสุขุมวิท กรุงเทพฯ'
})

const removeMember = (memberId) => {
  // TODO: DELETE /api/houses/{house.id}/members/{memberId}/
  members.value = members.value.filter(m => m.id !== memberId)
}

const saveSettings = () => {
  // TODO: PATCH /api/houses/{house.id}/
  houseName.value = houseSettings.value.name
  console.log('Saving settings:', houseSettings.value)
}

const refresh = () => {
  // TODO: GET /api/houses/{house.id}/members/
  console.log('Refreshing...')
}

onMounted(() => {
  // TODO: Load house members
})
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg);
}

.manage-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 768px) {
  .manage-grid {
    grid-template-columns: 1fr;
  }
}

.members-list {
  padding: 8px 0;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.member-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent-dim);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.member-info {
  flex: 1;
}

.member-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
}

.member-role {
  font-size: 12px;
  color: var(--text2);
}

.btn-remove {
  padding: 6px 12px;
  background: rgba(255, 77, 106, 0.1);
  color: var(--danger);
  border: 1px solid rgba(255, 77, 106, 0.2);
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.btn-remove:hover {
  background: rgba(255, 77, 106, 0.2);
}

.settings-form {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.settings-form .field label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: var(--text2);
  margin-bottom: 6px;
}
</style>
