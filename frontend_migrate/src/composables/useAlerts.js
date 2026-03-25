/**
 * Alerts composable
 * Handles alert rules, events, and notifications
 */
import { ref, computed } from 'vue'
import * as alertsApi from '../api/alerts'

// Shared state
const alertRules = ref([])
const alertEvents = ref([])
const notifications = ref([])
const isLoading = ref(false)
const error = ref(null)

export function useAlerts() {
  // Computed
  const hasRules = computed(() => alertRules.value.length > 0)
  const ruleCount = computed(() => alertRules.value.length)
  const activeRules = computed(() => 
    alertRules.value.filter(r => r.is_active)
  )
  const pendingEvents = computed(() => 
    alertEvents.value.filter(e => e.status === 'pending')
  )
  const pendingCount = computed(() => pendingEvents.value.length)
  const acknowledgedEvents = computed(() => 
    alertEvents.value.filter(e => e.status === 'acknowledged')
  )
  const dismissedEvents = computed(() => 
    alertEvents.value.filter(e => e.status === 'dismissed' || e.status === 'auto_resolved')
  )

  /**
   * Fetch all alert rules for a house
   * @param {string} houseId 
   * @returns {Promise<Array>}
   */
  async function fetchRules(houseId) {
    isLoading.value = true
    error.value = null

    try {
      const data = await alertsApi.getAlertRules(houseId)
      alertRules.value = data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch alert rules'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create an alert rule
   * @param {string} houseId 
   * @param {Object} data - {trigger: string, threshold_value?: number, action: string, plug_id?: string, device_id?: string}
   * @returns {Promise<Object>}
   */
  async function createRule(houseId, data) {
    isLoading.value = true
    error.value = null

    try {
      const newRule = await alertsApi.createAlertRule(houseId, data)
      alertRules.value.push(newRule)
      return newRule
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to create alert rule'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update an alert rule
   * @param {string} houseId 
   * @param {string} ruleId 
   * @param {Object} data 
   * @returns {Promise<Object>}
   */
  async function updateRule(houseId, ruleId, data) {
    isLoading.value = true
    error.value = null

    try {
      const updated = await alertsApi.updateAlertRule(houseId, ruleId, data)
      const index = alertRules.value.findIndex(r => r.id === ruleId)
      if (index !== -1) {
        alertRules.value[index] = updated
      }
      return updated
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to update alert rule'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete an alert rule
   * @param {string} houseId 
   * @param {string} ruleId 
   * @returns {Promise<void>}
   */
  async function deleteRule(houseId, ruleId) {
    isLoading.value = true
    error.value = null

    try {
      await alertsApi.deleteAlertRule(houseId, ruleId)
      alertRules.value = alertRules.value.filter(r => r.id !== ruleId)
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to delete alert rule'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch alert events for a house
   * @param {string} houseId 
   * @param {Object} params - {status?: string, limit?: number, offset?: number}
   * @returns {Promise<Object>}
   */
  async function fetchEvents(houseId, params = {}) {
    isLoading.value = true
    error.value = null

    try {
      const data = await alertsApi.getAlertEvents(houseId, params)
      alertEvents.value = data.results || data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch alert events'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Acknowledge an alert event
   * @param {string} houseId 
   * @param {string} eventId 
   * @returns {Promise<Object>}
   */
  async function acknowledgeEvent(houseId, eventId) {
    isLoading.value = true
    error.value = null

    try {
      const result = await alertsApi.alertEventAction(houseId, eventId, { action: 'acknowledge' })
      // Update local state
      const index = alertEvents.value.findIndex(e => e.id === eventId)
      if (index !== -1) {
        alertEvents.value[index] = { ...alertEvents.value[index], status: 'acknowledged' }
      }
      return result
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to acknowledge alert'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Snooze an alert event
   * @param {string} houseId 
   * @param {string} eventId 
   * @param {number} snoozeMinutes 
   * @returns {Promise<Object>}
   */
  async function snoozeEvent(houseId, eventId, snoozeMinutes = 30) {
    isLoading.value = true
    error.value = null

    try {
      const result = await alertsApi.alertEventAction(houseId, eventId, { 
        action: 'snooze', 
        snooze_minutes: snoozeMinutes 
      })
      // Update local state
      const index = alertEvents.value.findIndex(e => e.id === eventId)
      if (index !== -1) {
        alertEvents.value[index] = { 
          ...alertEvents.value[index], 
          status: 'snoozed',
          snooze_until: new Date(Date.now() + snoozeMinutes * 60000).toISOString()
        }
      }
      return result
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to snooze alert'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Dismiss an alert event
   * @param {string} houseId 
   * @param {string} eventId 
   * @returns {Promise<Object>}
   */
  async function dismissEvent(houseId, eventId) {
    isLoading.value = true
    error.value = null

    try {
      const result = await alertsApi.alertEventAction(houseId, eventId, { action: 'dismiss' })
      // Update local state
      const index = alertEvents.value.findIndex(e => e.id === eventId)
      if (index !== -1) {
        alertEvents.value[index] = { ...alertEvents.value[index], status: 'dismissed' }
      }
      return result
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to dismiss alert'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Auto-off action for an alert event
   * @param {string} houseId 
   * @param {string} eventId 
   * @returns {Promise<Object>}
   */
  async function autoOffEvent(houseId, eventId) {
    isLoading.value = true
    error.value = null

    try {
      const result = await alertsApi.alertEventAction(houseId, eventId, { action: 'auto_off' })
      // Update local state
      const index = alertEvents.value.findIndex(e => e.id === eventId)
      if (index !== -1) {
        alertEvents.value[index] = { ...alertEvents.value[index], status: 'auto_resolved' }
      }
      return result
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to auto-off'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Register push notification token
   * @param {Object} data - {token: string, platform: 'fcm'|'apns', device_label?: string}
   * @returns {Promise<Object>}
   */
  async function registerPushToken(data) {
    isLoading.value = true
    error.value = null

    try {
      const result = await alertsApi.registerPushToken(data)
      return result
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to register push token'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete push notification token
   * @param {string} token 
   * @returns {Promise<Object>}
   */
  async function deletePushToken(token) {
    isLoading.value = true
    error.value = null

    try {
      const result = await alertsApi.deletePushToken({ token })
      return result
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to delete push token'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch user notifications
   * @returns {Promise<Array>}
   */
  async function fetchNotifications() {
    isLoading.value = true
    error.value = null

    try {
      const data = await alertsApi.getUserNotifications()
      notifications.value = data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch notifications'
      throw err
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

  /**
   * Reset state
   */
  function reset() {
    alertRules.value = []
    alertEvents.value = []
    notifications.value = []
    error.value = null
  }

  return {
    // State
    alertRules,
    alertEvents,
    notifications,
    isLoading,
    error,
    // Computed
    hasRules,
    ruleCount,
    activeRules,
    pendingEvents,
    pendingCount,
    acknowledgedEvents,
    dismissedEvents,
    // Rule methods
    fetchRules,
    createRule,
    updateRule,
    deleteRule,
    // Event methods
    fetchEvents,
    acknowledgeEvent,
    snoozeEvent,
    dismissEvent,
    autoOffEvent,
    // Push methods
    registerPushToken,
    deletePushToken,
    // Notification methods
    fetchNotifications,
    // Utility
    clearError,
    reset,
  }
}
