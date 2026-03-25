<template>
  <div class="auth-page">
    <div class="auth-wrap">
      <div class="auth-card" style="text-align: center;">
        <!-- Loading state -->
        <div v-if="verificationState === 'loading'">
          <div class="state-icon loading"></div>
          <p class="auth-subhead">Verifying your email…</p>
        </div>

        <!-- Success state -->
        <div v-else-if="verificationState === 'success'">
          <div class="state-icon success">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <h1 class="auth-headline">Email verified!</h1>
          <p class="auth-subhead">Your account is now active. You can sign in to access your dashboard.</p>
          <RouterLink to="/login" class="btn-primary" style="display: block; margin-top: 20px;">Sign In</RouterLink>
        </div>

        <!-- Error state -->
        <div v-else-if="verificationState === 'error'">
          <div class="state-icon error">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
          </div>
          <h1 class="auth-headline">Verification failed</h1>
          <p class="auth-subhead">{{ errorMessage }}</p>
          <RouterLink to="/login" class="btn-primary" style="display: block; margin-top: 20px;">Back to Sign In</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuth } from '../../composables/useAuth'

const route = useRoute()

const { verifyEmail: verifyEmailApi } = useAuth()

const verificationState = ref('loading')
const errorMessage = ref('The verification link is invalid or has expired.')

const verifyEmail = async () => {
  const token = route.query.token
  
  if (!token) {
    verificationState.value = 'error'
    errorMessage.value = 'No verification token provided.'
    return
  }
  
  try {
    const result = await verifyEmailApi(token)
    
    if (result.success) {
      verificationState.value = 'success'
    } else {
      verificationState.value = 'error'
      errorMessage.value = result.message || 'Verification failed. The link may be expired or invalid.'
    }
  } catch (err) {
    verificationState.value = 'error'
    errorMessage.value = 'Verification failed. The link may be expired or invalid.'
  }
}

onMounted(() => {
  verifyEmail()
})
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
