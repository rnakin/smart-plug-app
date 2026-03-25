/**
 * Authentication API endpoints
 */
import client from './client'

/**
 * Login with username and password
 * @param {string} username 
 * @param {string} password 
 * @returns {Promise<{access: string, refresh: string}>}
 */
export async function login(username, password) {
  const response = await client.post('/auth/login/', { username, password })
  return response.data
}

/**
 * Register a new user
 * @param {string} username 
 * @param {string} email 
 * @param {string} password 
 * @returns {Promise<{message: string}>}
 */
export async function register(username, email, password) {
  const response = await client.post('/auth/register/', { username, email, password })
  return response.data
}

/**
 * Logout - blacklist the refresh token
 * @param {string} refreshToken 
 * @returns {Promise<{message: string}>}
 */
export async function logout(refreshToken) {
  const response = await client.post('/auth/logout/', { refresh: refreshToken })
  return response.data
}

/**
 * Refresh the access token
 * @param {string} refreshToken 
 * @returns {Promise<{access: string}>}
 */
export async function refreshToken(refreshToken) {
  const response = await client.post('/auth/refresh/', { refresh: refreshToken })
  return response.data
}

/**
 * Get current user info
 * @returns {Promise<{id: string, username: string, email: string}>}
 */
export async function getMe() {
  const response = await client.get('/auth/me/')
  return response.data
}

/**
 * Update current user profile
 * @param {Object} data - {username?, email?, current_password?, new_password?}
 * @returns {Promise<{message: string, username: string, email: string}>}
 */
export async function updateProfile(data) {
  const response = await client.patch('/auth/me/update/', data)
  return response.data
}

/**
 * Request password reset email
 * @param {string} email 
 * @returns {Promise<{message: string}>}
 */
export async function forgotPassword(email) {
  const response = await client.post('/auth/forgot-password/', { email })
  return response.data
}

/**
 * Reset password with token
 * @param {string} token 
 * @param {string} password 
 * @returns {Promise<{message: string}>}
 */
export async function resetPassword(token, password) {
  const response = await client.post('/auth/reset-password/', { token, password })
  return response.data
}

/**
 * Verify email with token
 * @param {string} token 
 * @returns {Promise<{message: string}>}
 */
export async function verifyEmail(token) {
  const response = await client.post('/auth/verify-email/', { token })
  return response.data
}

/**
 * Resend verification email
 * @param {string} email 
 * @returns {Promise<{message: string}>}
 */
export async function resendVerification(email) {
  const response = await client.post('/auth/resend-verification/', { email })
  return response.data
}
