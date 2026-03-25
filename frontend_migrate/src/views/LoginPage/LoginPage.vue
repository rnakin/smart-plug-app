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

        <h1 class="auth-headline">Welcome back</h1>
        <p class="auth-subhead">Sign in to your account</p>

        <div class="field-group">
          <div class="field">
            <label for="username">Username</label>
            <input 
              id="username" 
              v-model="username" 
              type="text" 
              placeholder="Enter your username" 
              autocomplete="username"
              @keyup.enter="handleLogin"
            >
          </div>
          <div class="field">
            <label for="password">Password</label>
            <input 
              id="password" 
              v-model="password" 
              type="password" 
              placeholder="Enter your password" 
              autocomplete="current-password"
              @keyup.enter="handleLogin"
            >
          </div>
        </div>

        <p class="msg-error">{{ errorMessage }}</p>

        <button class="btn-primary" @click="handleLogin">Sign In</button>

        <div class="auth-footer" style="margin-top:14px;">
          <RouterLink to="/forgot-password">Forgot password?</RouterLink>
        </div>
        <div class="auth-footer">
          Don't have an account? <RouterLink to="/register">Create one</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const password = ref('')
const errorMessage = ref('')

// TODO: Replace with POST /auth/login/ API call
const handleLogin = () => {
  errorMessage.value = ''
  
  if (!username.value || !password.value) {
    errorMessage.value = 'Please enter both username and password'
    return
  }
  
  // TODO: Implement actual authentication
  // TODO: Store JWT tokens in localStorage
  // TODO: Redirect to /home on success
  console.log('Login attempt:', { username: username.value, password: password.value })
  
  // Placeholder: Navigate to home
  router.push('/home')
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
