<template>
  <div class="dashboard-layout">
    <Sidebar />
    <div class="center-panel">
      <div class="top-bar">
        <div>
          <div class="top-bar-title">👤 บัญชีของฉัน</div>
          <div class="top-bar-sub">{{ username }}</div>
        </div>
      </div>

      <div class="dashboard-content">
        <div class="account-content">
          <!-- Profile Card -->
          <div class="card" style="margin-bottom: 16px;">
            <div class="card-header">
              <div class="card-title">ข้อมูลบัญชี</div>
            </div>
            <div class="form-section">
              <div class="field">
                <label>ชื่อผู้ใช้</label>
                <input v-model="profile.username" type="text" class="modal-input" placeholder="ชื่อผู้ใช้">
              </div>
              <div class="field">
                <label>อีเมล</label>
                <input v-model="profile.email" type="email" class="modal-input" placeholder="อีเมล">
              </div>
              <p class="form-message">{{ profileMessage }}</p>
              <button class="btn btn-accent" @click="saveProfile">บันทึกข้อมูล</button>
            </div>
          </div>

          <!-- Password Card -->
          <div class="card">
            <div class="card-header">
              <div class="card-title">เปลี่ยนรหัสผ่าน</div>
            </div>
            <div class="form-section">
              <div class="field">
                <label>รหัสผ่านปัจจุบัน</label>
                <input v-model="password.current" type="password" class="modal-input" placeholder="รหัสผ่านปัจจุบัน">
              </div>
              <div class="field">
                <label>รหัสผ่านใหม่</label>
                <input v-model="password.new" type="password" class="modal-input" placeholder="รหัสผ่านใหม่">
              </div>
              <div class="field">
                <label>ยืนยันรหัสผ่านใหม่</label>
                <input v-model="password.confirm" type="password" class="modal-input" placeholder="ยืนยันรหัสผ่านใหม่">
              </div>
              <p class="form-message">{{ passwordMessage }}</p>
              <button class="btn btn-accent" @click="changePassword">เปลี่ยนรหัสผ่าน</button>
            </div>
          </div>

          <!-- Logout -->
          <div style="margin-top: 16px;">
            <button class="btn-logout" @click="logout">
              ออกจากระบบ
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Sidebar from '../../components/Sidebar/Sidebar.vue'
import { useAuth } from '../../composables/useAuth'

// Composables
const { 
  user, 
  username, 
  fetchUser, 
  updateProfile, 
  logout: authLogout,
  isLoading,
  error 
} = useAuth()

// State
const profile = ref({
  username: '',
  email: ''
})
const password = ref({
  current: '',
  new: '',
  confirm: ''
})
const profileMessage = ref('')
const passwordMessage = ref('')

// Methods
const saveProfile = async () => {
  profileMessage.value = ''
  
  try {
    const result = await updateProfile({
      username: profile.value.username,
      email: profile.value.email
    })
    
    if (result.success) {
      profileMessage.value = 'บันทึกข้อมูลสำเร็จ'
      setTimeout(() => profileMessage.value = '', 3000)
    } else {
      profileMessage.value = result.message
    }
  } catch (err) {
    profileMessage.value = 'เกิดข้อผิดพลาดในการบันทึก'
  }
}

const changePassword = async () => {
  passwordMessage.value = ''
  
  // Validate passwords match
  if (password.value.new !== password.value.confirm) {
    passwordMessage.value = 'รหัสผ่านไม่ตรงกัน'
    return
  }
  
  // Validate password length
  if (password.value.new.length < 8) {
    passwordMessage.value = 'รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร'
    return
  }
  
  try {
    const result = await updateProfile({
      current_password: password.value.current,
      new_password: password.value.new
    })
    
    if (result.success) {
      passwordMessage.value = 'เปลี่ยนรหัสผ่านสำเร็จ'
      password.value = { current: '', new: '', confirm: '' }
      setTimeout(() => passwordMessage.value = '', 3000)
    } else {
      passwordMessage.value = result.message
    }
  } catch (err) {
    passwordMessage.value = 'เกิดข้อผิดพลาดในการเปลี่ยนรหัสผ่าน'
  }
}

const logout = async () => {
  await authLogout()
}

// Initialize on mount
onMounted(async () => {
  // Fetch user info if not already loaded
  if (!user.value) {
    await fetchUser()
  }
  
  // Initialize profile form with user data
  if (user.value) {
    profile.value.username = user.value.username || ''
    profile.value.email = user.value.email || ''
  }
})
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg);
}

.account-content {
  max-width: 480px;
}

.form-section {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-section .field label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: var(--text2);
  margin-bottom: 6px;
}

.form-message {
  font-size: 12px;
  min-height: 16px;
  margin: 0;
  color: var(--accent);
}

.btn-logout {
  width: 100%;
  padding: 12px;
  background: rgba(255, 77, 106, 0.1);
  border: 1px solid rgba(255, 77, 106, 0.3);
  border-radius: 10px;
  color: var(--danger);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: 'DM Sans', sans-serif;
}

.btn-logout:hover {
  background: rgba(255, 77, 106, 0.2);
}
</style>
