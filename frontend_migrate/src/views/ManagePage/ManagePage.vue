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
              <div v-for="member in displayMembers" :key="member.id" class="member-item">
                <div class="member-avatar">{{ member.name[0] }}</div>
                <div class="member-info">
                  <div class="member-name">{{ member.name }}</div>
                  <div class="member-role">{{ member.role }}</div>
                </div>
                <button v-if="!member.isOwner" class="btn-remove" @click="removeMember(member.id)">
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
import { ref, computed, onMounted } from 'vue'
import Sidebar from '../../components/Sidebar/Sidebar.vue'
import { useHouses } from '../../composables/useHouses'

// Composables
const { 
  houses, 
  fetchHouses, 
  currentHouse, 
  setCurrentHouse,
  fetchMembers,
  members,
  removeMember: deleteMember,
  updateHouse,
  loading,
  error
} = useHouses()

// State
const showAddMember = ref(false)
const activeHouseId = ref(null)

// Computed
const houseName = computed(() => currentHouse.value?.name || 'เลือกบ้าน')

const houseSettings = ref({
  name: '',
  address: ''
})

// Role label mapping
const roleLabel = (role) => {
  const map = { owner: 'เจ้าของ', admin: 'ผู้ดูแล', member: 'สมาชิก', guest: 'แขก' }
  return map[role] || role
}

// Computed members with role labels
const displayMembers = computed(() => {
  if (!members.value || members.value.length === 0) {
    return []
  }
  return members.value.map(m => ({
    id: m.id,
    name: m.user?.username || m.user?.email || 'Unknown',
    role: roleLabel(m.role),
    isOwner: m.role === 'owner'
  }))
})

// Methods
const removeMember = async (memberId) => {
  if (!activeHouseId.value) return
  
  try {
    await deleteMember(activeHouseId.value, memberId)
    // Members list is automatically updated in the composable
  } catch (err) {
    console.error('Error removing member:', err)
  }
}

const saveSettings = async () => {
  if (!activeHouseId.value) return
  
  try {
    await updateHouse(activeHouseId.value, {
      name: houseSettings.value.name,
      address: houseSettings.value.address
    })
    // House is automatically updated in the composable
  } catch (err) {
    console.error('Error saving settings:', err)
  }
}

const refresh = async () => {
  if (!activeHouseId.value) return
  
  try {
    await fetchMembers(activeHouseId.value)
  } catch (err) {
    console.error('Error refreshing:', err)
  }
}

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
      if (house) {
        setCurrentHouse(house)
        // Initialize settings form with current house data
        houseSettings.value = {
          name: house.name || '',
          address: house.address || ''
        }
      }
    } else if (houses.value.length > 0) {
      activeHouseId.value = houses.value[0].id
      setCurrentHouse(houses.value[0])
      houseSettings.value = {
        name: houses.value[0].name || '',
        address: houses.value[0].address || ''
      }
    }
    
    // Load members
    if (activeHouseId.value) {
      await fetchMembers(activeHouseId.value)
    }
  } catch (err) {
    console.error('Error initializing manage page:', err)
  }
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
