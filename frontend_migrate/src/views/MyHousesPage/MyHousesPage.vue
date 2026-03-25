<template>
  <div class="dashboard-layout">
    <Sidebar />
    <div class="center-panel">
      <div class="top-bar">
        <div>
          <div class="top-bar-title">🔑 บ้านของฉัน</div>
          <div class="top-bar-sub">บ้านทั้งหมดที่คุณเป็นสมาชิก</div>
        </div>
        <div class="top-bar-actions">
          <button class="btn btn-ghost" @click="refresh">รีเฟรช</button>
        </div>
      </div>

      <div class="dashboard-content">
        <div class="houses-grid">
          <div v-for="house in houses" :key="house.id" class="house-card">
            <div class="house-emoji">{{ house.emoji || '🏠' }}</div>
            <div class="house-info">
              <div class="house-name">{{ house.house_name }}</div>
              <div class="house-address">{{ house.address }}</div>
              <div class="house-role" :class="house.role">{{ roleLabel(house.role) }}</div>
            </div>
            <div class="house-actions">
              <button class="btn btn-ghost" @click="selectHouse(house)">เข้าสู่บ้าน</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from '../../components/Sidebar/Sidebar.vue'

const router = useRouter()

const houses = ref([
  { id: 1, house_name: 'บ้านสุขสบาย', address: '123 ถนนสุขุมวิท กรุงเทพฯ', emoji: '🏠', role: 'owner' },
  { id: 2, house_name: 'ออฟฟิศ', address: '456 ถนนสีลม กรุงเทพฯ', emoji: '🏢', role: 'admin' },
  { id: 3, house_name: 'บ้านพักตากอากาศ', address: '789 ถนนชายทะเล ชลบุรี', emoji: '🏡', role: 'member' }
])

const roleLabel = (role) => {
  const map = { owner: 'เจ้าของ', admin: 'ผู้ดูแล', member: 'สมาชิก', guest: 'แขก' }
  return map[role] || role
}

const selectHouse = (house) => {
  // TODO: Set active house and redirect
  router.push('/home')
}

const refresh = () => {
  // TODO: GET /api/houses/
  console.log('Refreshing houses...')
}

onMounted(() => {
  // TODO: Load all houses where user is a member
})
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg);
}

.houses-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.house-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
}

.house-emoji {
  font-size: 40px;
}

.house-info {
  flex: 1;
}

.house-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
}

.house-address {
  font-size: 12px;
  color: var(--text2);
  margin-bottom: 8px;
}

.house-role {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
}

.house-role.owner {
  background: var(--accent-dim);
  color: var(--accent);
}

.house-role.admin {
  background: rgba(77, 159, 255, 0.1);
  color: var(--accent2);
}

.house-role.member {
  background: var(--surface3);
  color: var(--text2);
}
</style>
