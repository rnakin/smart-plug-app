<template>
  <nav class="sidebar">
    <div class="logo" @click="navigateTo('home')" style="cursor: pointer;">
      <svg width="20" height="20" fill="none" viewBox="0 0 24 24">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke="var(--accent)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>

    <button 
      class="nav-btn" 
      :class="{ active: activePage === 'home' }"
      @click="navigateTo('home')"
      title="หน้าหลัก"
    >
      <svg width="19" height="19" fill="none" viewBox="0 0 24 24">
        <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" stroke-width="1.8"/>
        <polyline points="9 22 9 12 15 12 15 22" stroke="currentColor" stroke-width="1.8"/>
      </svg>
    </button>

    <button 
      class="nav-btn" 
      :class="{ active: activePage === 'dashboard' }"
      @click="navigateTo('dashboard')"
      title="Dashboard"
    >
      <svg width="19" height="19" fill="none" viewBox="0 0 24 24">
        <rect x="3" y="3" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="1.8"/>
        <rect x="14" y="3" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="1.8"/>
        <rect x="3" y="14" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="1.8"/>
        <rect x="14" y="14" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="1.8"/>
      </svg>
    </button>

    <button 
      class="nav-btn" 
      :class="{ active: activePage === 'energy' }"
      @click="navigateTo('energy')"
      title="พลังงาน"
    >
      <svg width="19" height="19" fill="none" viewBox="0 0 24 24">
        <path d="M3 3v18h18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        <path d="m7 16 4-5 4 3 4-6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <button 
      class="nav-btn" 
      :class="{ active: activePage === 'alerts' }"
      @click="navigateTo('alerts')"
      title="การแจ้งเตือน"
      style="position: relative;"
    >
      <svg width="19" height="19" fill="none" viewBox="0 0 24 24">
        <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        <path d="M13.73 21a2 2 0 01-3.46 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
      <div v-if="alertCount > 0" class="bdg">
        {{ alertCount > 9 ? '9+' : alertCount }}
      </div>
    </button>

    <div class="sidebar-gap"></div>

    <button class="theme-btn" @click="toggleTheme" title="สลับธีม">
      <svg v-if="isDark" class="i-sun" width="17" height="17" fill="none" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="5" stroke="currentColor" stroke-width="1.8"/>
        <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
      <svg v-else class="i-moon" width="17" height="17" fill="none" viewBox="0 0 24 24">
        <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </button>

    <div class="avatar" title="โปรไฟล์">
      {{ userInitials }}
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../../composables/useAuth'
import { useAlerts } from '../../composables/useAlerts'

const router = useRouter()
const route = useRoute()

// Composables
const { user, username, fetchUser } = useAuth()
const { fetchAlertEvents, alertEvents } = useAlerts()

// State
const isDark = ref(true)
let refreshInterval = null

// Computed
const userInitials = computed(() => {
  return (username.value || 'U').slice(0, 1).toUpperCase()
})

const alertCount = computed(() => {
  return alertEvents.value?.filter(e => e.status === 'pending').length || 0
})

const activePage = computed(() => {
  const path = route.path
  if (path === '/home') return 'home'
  if (path === '/dashboard') return 'dashboard'
  if (path === '/energy') return 'energy'
  if (path === '/alerts') return 'alerts'
  return ''
})

// Methods
const navigateTo = (page) => {
  router.push(`/${page}`)
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

const fetchAlertCount = async () => {
  // Get active house from localStorage
  const activeHouseId = localStorage.getItem('activeHouseId')
  if (!activeHouseId) return
  
  try {
    await fetchAlertEvents(activeHouseId, { status: 'pending' })
  } catch (err) {
    console.error('Error fetching alert count:', err)
  }
}

// Lifecycle
onMounted(async () => {
  // Restore saved theme
  const savedTheme = localStorage.getItem('theme') || 'dark'
  isDark.value = savedTheme === 'dark'
  document.documentElement.setAttribute('data-theme', savedTheme)
  
  // Fetch current user info if not already loaded
  if (!user.value) {
    await fetchUser()
  }
  
  // Fetch alert badge
  await fetchAlertCount()
  
  // Refresh badge every 30s
  refreshInterval = setInterval(fetchAlertCount, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
@import './Sidebar.css';
</style>
