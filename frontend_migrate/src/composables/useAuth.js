/**
 * Authentication composable
 * Handles login, logout, registration, and user state
 */
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as authApi from '../api/auth'

// Shared state
const user = ref(null)
const isLoading = ref(false)
const error = ref(null)

// Initialize user from localStorage
const storedUser = localStorage.getItem('user')
if (storedUser) {
  try {
    user.value = JSON.parse(storedUser)
  } catch {
    localStorage.removeItem('user')
  }
}

export function useAuth() {
  const router = useRouter()

  // Computed properties
  const isAuthenticated = computed(() => !!user.value && !!localStorage.getItem('access_token'))
  const username = computed(() => user.value?.username || '')

  /**
   * Login with username and password
   * @param {string} usernameInput 
   * @param {string} password 
   * @returns {Promise<boolean>}
   */
  async function login(usernameInput, password) {
    isLoading.value = true
    error.value = null

    try {
      const data = await authApi.login(usernameInput, password)
      
      // Store tokens
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)

      // Fetch user info
      const userInfo = await authApi.getMe()
      user.value = userInfo
      localStorage.setItem('user', JSON.stringify(userInfo))

      return true
    } catch (err) {
      error.value = err.response?.data?.error || err.response?.data?.detail || 'Login failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Register a new user
   * @param {string} usernameInput 
   * @param {string} email 
   * @param {string} password 
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async function register(usernameInput, email, password) {
    isLoading.value = true
    error.value = null

    try {
      const data = await authApi.register(usernameInput, email, password)
      return { success: true, message: data.message }
    } catch (err) {
      const errorMsg = err.response?.data?.error
      if (Array.isArray(errorMsg)) {
        error.value = errorMsg.join(', ')
      } else {
        error.value = errorMsg || 'Registration failed'
      }
      return { success: false, message: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Logout the current user
   */
  async function logout() {
    const refreshToken = localStorage.getItem('refresh_token')
    
    try {
      if (refreshToken) {
        await authApi.logout(refreshToken)
      }
    } catch {
      // Ignore logout errors
    }

    // Clear local state
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    user.value = null

    router.push('/login')
  }

  /**
   * Fetch current user info
   * @returns {Promise<void>}
   */
  async function fetchUser() {
    if (!localStorage.getItem('access_token')) {
      return
    }

    isLoading.value = true
    try {
      const userInfo = await authApi.getMe()
      user.value = userInfo
      localStorage.setItem('user', JSON.stringify(userInfo))
    } catch (err) {
      // Token might be invalid, clear state
      if (err.response?.status === 401) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        user.value = null
      }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update user profile
   * @param {Object} data 
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async function updateProfile(data) {
    isLoading.value = true
    error.value = null

    try {
      const result = await authApi.updateProfile(data)
      
      // Update local user state
      if (user.value) {
        user.value = { ...user.value, username: result.username, email: result.email }
        localStorage.setItem('user', JSON.stringify(user.value))
      }

      return { success: true, message: result.message }
    } catch (err) {
      const errorMsg = err.response?.data?.error
      if (Array.isArray(errorMsg)) {
        error.value = errorMsg.join(', ')
      } else {
        error.value = errorMsg || 'Update failed'
      }
      return { success: false, message: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Request password reset
   * @param {string} email 
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async function forgotPassword(email) {
    isLoading.value = true
    error.value = null

    try {
      const data = await authApi.forgotPassword(email)
      return { success: true, message: data.message }
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to send reset email'
      return { success: false, message: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Reset password with token
   * @param {string} token 
   * @param {string} password 
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async function resetPassword(token, password) {
    isLoading.value = true
    error.value = null

    try {
      const data = await authApi.resetPassword(token, password)
      return { success: true, message: data.message }
    } catch (err) {
      error.value = err.response?.data?.error || 'Password reset failed'
      return { success: false, message: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Verify email with token
   * @param {string} token 
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async function verifyEmail(token) {
    isLoading.value = true
    error.value = null

    try {
      const data = await authApi.verifyEmail(token)
      return { success: true, message: data.message }
    } catch (err) {
      error.value = err.response?.data?.error || 'Email verification failed'
      return { success: false, message: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Resend verification email
   * @param {string} email 
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async function resendVerification(email) {
    isLoading.value = true
    error.value = null

    try {
      const data = await authApi.resendVerification(email)
      return { success: true, message: data.message }
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to resend verification'
      return { success: false, message: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Clear error
   */
  function clearError() {
    error.value = null
  }

  return {
    // State
    user,
    isLoading,
    error,
    // Computed
    isAuthenticated,
    username,
    // Methods
    login,
    register,
    logout,
    fetchUser,
    updateProfile,
    forgotPassword,
    resetPassword,
    verifyEmail,
    resendVerification,
    clearError,
  }
}
