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

        <!-- Registration form -->
        <div v-if="!showSuccess">
          <h1 class="auth-headline">Create account</h1>
          <p class="auth-subhead">Start monitoring your energy usage</p>

          <div class="field-group">
            <div class="field">
              <label for="username">Username</label>
              <input 
                id="username" 
                v-model="username" 
                type="text" 
                placeholder="Choose a username" 
                autocomplete="username"
                @keyup.enter="handleRegister"
              >
            </div>
            <div class="field">
              <label for="email">Email</label>
              <input 
                id="email" 
                v-model="email" 
                type="email" 
                placeholder="your@email.com" 
                autocomplete="email"
                @keyup.enter="handleRegister"
              >
            </div>
            <div class="field">
              <label for="password">Password</label>
              <input 
                id="password" 
                v-model="password" 
                type="password" 
                placeholder="Create a password" 
                autocomplete="new-password"
                @keyup.enter="handleRegister"
              >
            </div>
          </div>

          <p class="msg-error">{{ errorMessage }}</p>

          <button class="btn-primary" @click="handleRegister">Create Account</button>

          <div class="auth-footer">
            Already have an account? <RouterLink to="/login">Sign in</RouterLink>
          </div>
        </div>

        <!-- Check email state -->
        <div v-else style="text-align: center;">
          <div class="success-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              <polyline points="22,6 12,13 2,6"/>
            </svg>
          </div>
          <h1 class="auth-headline" style="margin-bottom:8px;">Check your email</h1>
          <p class="auth-subhead" style="margin-bottom:0;">
            We sent a verification link to <strong style="color:var(--text)">{{ email }}</strong>.<br>
            Click the link to activate your account.<br>
            If you don't get it, 
            <button 
              @click="resendVerification" 
              style="color:var(--accent); background:none; border:none; cursor:pointer; font-size:13px; font-family:inherit; padding:0;"
            >
              resend
            </button>.
          </p>
          <div class="auth-footer" style="margin-top:24px;">
            <RouterLink to="/login">← Back to sign in</RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuth } from '../../composables/useAuth'

const { register, resendVerification: resendVerificationApi, error } = useAuth()

const username = ref('')
const email = ref('')
const password = ref('')
const errorMessage = ref('')
const showSuccess = ref(false)

const handleRegister = async () => {
  errorMessage.value = ''
  
  if (!username.value || !email.value || !password.value) {
    errorMessage.value = 'All fields are required.'
    return
  }
  
  const result = await register(username.value, email.value, password.value)
  
  if (result.success) {
    showSuccess.value = true
  } else {
    errorMessage.value = result.message
  }
}

const resendVerification = async () => {
  const result = await resendVerificationApi(email.value)
  if (result.success) {
    alert('Verification email sent!')
  } else {
    alert(result.message || 'Failed to resend verification')
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
