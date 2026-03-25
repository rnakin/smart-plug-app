<template>
  <div class="auth-page">
    <div class="auth-wrap">
      <div class="auth-card">
        <div class="auth-logo">
          <div class="auth-logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
            </svg>
          </div>
          <span class="auth-logo-name">KnowWatt</span>
        </div>

        <h1 class="auth-headline">New password</h1>
        <p class="auth-subhead">Choose a strong password for your account</p>

        <div class="field-group">
          <div class="field">
            <label for="password">New password</label>
            <input 
              id="password" 
              v-model="password" 
              type="password" 
              placeholder="Enter new password" 
              autocomplete="new-password"
              @keyup.enter="resetPassword"
            >
          </div>
          <div class="field">
            <label for="confirm">Confirm password</label>
            <input 
              id="confirm" 
              v-model="confirmPassword" 
              type="password" 
              placeholder="Confirm new password" 
              autocomplete="new-password"
              @keyup.enter="resetPassword"
            >
          </div>
        </div>

        <p class="msg-error">{{ errorMessage }}</p>
        <p class="msg-notice">{{ noticeMessage }}</p>

        <button 
          class="btn-primary" 
          :disabled="!isValidToken"
          @click="resetPassword"
        >
          Set New Password
        </button>

        <div class="auth-footer">
          <RouterLink to="/login">← Back to sign in</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuth } from '../../composables/useAuth'

const route = useRoute()
const router = useRouter()

const { resetPassword: resetPasswordApi, isLoading, error } = useAuth()

const password = ref('')
const confirmPassword = ref('')
const errorMessage = ref('')
const noticeMessage = ref('')
const token = ref('')

const isValidToken = computed(() => {
  return !!token.value
})

onMounted(() => {
  // Extract token from URL: /reset-password?token=xxx
  token.value = route.query.token || ''
  
  if (!token.value) {
    errorMessage.value = 'Invalid or missing reset token.'
  }
})

const resetPassword = async () => {
  errorMessage.value = ''
  noticeMessage.value = ''
  
  if (!password.value) {
    errorMessage.value = 'Password is required.'
    return
  }
  
  if (password.value.length < 8) {
    errorMessage.value = 'Password must be at least 8 characters.'
    return
  }
  
  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match.'
    return
  }
  
  try {
    const result = await resetPasswordApi(token.value, password.value)
    
    if (result.success) {
      noticeMessage.value = 'Password reset successful. Redirecting...'
      
      // Redirect to login after successful reset
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    } else {
      errorMessage.value = result.message
    }
  } catch (err) {
    errorMessage.value = 'Failed to reset password. Please try again.'
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  overflow: auto;
  background: var(--bg);
}
</style>
