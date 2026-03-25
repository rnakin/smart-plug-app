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

        <h1 class="auth-headline">Reset password</h1>
        <p class="auth-subhead">Enter your email and we'll send you a reset link</p>

        <div class="field-group">
          <div class="field">
            <label for="email">Email address</label>
            <input 
              id="email" 
              v-model="email" 
              type="email" 
              placeholder="your@email.com" 
              autocomplete="email"
              @keyup.enter="sendReset"
            >
          </div>
        </div>

        <p class="msg-error">{{ errorMessage }}</p>
        <p class="msg-notice">{{ noticeMessage }}</p>

        <button class="btn-primary" @click="sendReset">Send Reset Link</button>

        <div class="auth-footer">
          <RouterLink to="/login">← Back to sign in</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuth } from '../../composables/useAuth'

const { forgotPassword, isLoading, error } = useAuth()

const email = ref('')
const errorMessage = ref('')
const noticeMessage = ref('')

const sendReset = async () => {
  errorMessage.value = ''
  noticeMessage.value = ''
  
  if (!email.value) {
    errorMessage.value = 'Please enter your email address'
    return
  }
  
  try {
    const result = await forgotPassword(email.value)
    
    if (result.success) {
      noticeMessage.value = 'If that email exists, a reset link has been sent.'
      email.value = ''
    } else {
      errorMessage.value = result.message
    }
  } catch (err) {
    errorMessage.value = 'Failed to send reset link. Please try again.'
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
