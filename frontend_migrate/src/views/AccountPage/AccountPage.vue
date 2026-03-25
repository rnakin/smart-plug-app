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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Sidebar from '../../components/Sidebar/Sidebar.vue'

const router = useRouter()

const username = ref('ผู้ใช้')
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

const saveProfile = () => {
  // TODO: PATCH /auth/me/
  profileMessage.value = 'บันทึกข้อมูลสำเร็จ'
  setTimeout(() => profileMessage.value = '', 3000)
}

const changePassword = () => {
  // TODO: POST /auth/change-password/
  if (password.value.new !== password.value.confirm) {
    passwordMessage.value = 'รหัสผ่านไม่ตรงกัน'
    return
  }
  passwordMessage.value = 'เปลี่ยนรหัสผ่านสำเร็จ'
  password.value = { current: '', new: '', confirm: '' }
  setTimeout(() => passwordMessage.value = '', 3000)
}

const logout = () => {
  // TODO: Clear localStorage and JWT tokens
  // TODO: POST /auth/logout/
  localStorage.removeItem('access')
  localStorage.removeItem('refresh')
  router.push('/login')
}

onMounted(() => {
  // TODO: GET /auth/me/
  profile.value.username = username.value
  profile.value.email = 'user@example.com'
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
