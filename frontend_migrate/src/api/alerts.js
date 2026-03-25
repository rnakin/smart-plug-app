/**
 * Alerts API endpoints
 */
import client from './client'

/**
 * Get all alert rules for a house
 * @param {string} houseId 
 * @returns {Promise<Array<{id: string, house_id: string, plug_id: string, plug_name: string, device_id: string, device_name: string, trigger: string, threshold_value: number, action: string, is_active: boolean, created_at: string}>>}
 */
export async function getAlertRules(houseId) {
  const response = await client.get(`/houses/${houseId}/alerts/rules/`)
  return response.data
}

/**
 * Create an alert rule
 * @param {string} houseId 
 * @param {Object} data - {trigger: string, threshold_value?: number, action: string, plug_id?: string, device_id?: string}
 * @returns {Promise<{id: string, house_id: string, plug_id: string, plug_name: string, device_id: string, device_name: string, trigger: string, threshold_value: number, action: string, is_active: boolean, created_at: string}>}
 */
export async function createAlertRule(houseId, data) {
  const response = await client.post(`/houses/${houseId}/alerts/rules/`, data)
  return response.data
}

/**
 * Get alert rule details
 * @param {string} houseId 
 * @param {string} ruleId 
 * @returns {Promise<{id: string, house_id: string, plug_id: string, plug_name: string, device_id: string, device_name: string, trigger: string, threshold_value: number, action: string, is_active: boolean, created_at: string}>}
 */
export async function getAlertRule(houseId, ruleId) {
  const response = await client.get(`/houses/${houseId}/alerts/rules/${ruleId}/`)
  return response.data
}

/**
 * Update an alert rule
 * @param {string} houseId 
 * @param {string} ruleId 
 * @param {Object} data - {trigger?: string, threshold_value?: number, action?: string, is_active?: boolean}
 * @returns {Promise<{id: string, house_id: string, plug_id: string, plug_name: string, device_id: string, device_name: string, trigger: string, threshold_value: number, action: string, is_active: boolean, created_at: string}>}
 */
export async function updateAlertRule(houseId, ruleId, data) {
  const response = await client.patch(`/houses/${houseId}/alerts/rules/${ruleId}/`, data)
  return response.data
}

/**
 * Delete an alert rule
 * @param {string} houseId 
 * @param {string} ruleId 
 * @returns {Promise<{message: string}>}
 */
export async function deleteAlertRule(houseId, ruleId) {
  const response = await client.delete(`/houses/${houseId}/alerts/rules/${ruleId}/`)
  return response.data
}

/**
 * Get alert events for a house
 * @param {string} houseId 
 * @param {Object} params - {status?: 'pending'|'acknowledged'|'snoozed'|'dismissed'|'auto_resolved', limit?: number, offset?: number}
 * @returns {Promise<{total: number, limit: number, offset: number, results: Array<{id: string, house_id: string, rule_id: string, plug_id: string, plug_name: string, device_id: string, device_name: string, title: string, message: string, trigger_value: number, status: string, triggered_at: string, resolved_at: string, snooze_until: string, push_sent: boolean}>}>}
 */
export async function getAlertEvents(houseId, params = {}) {
  const response = await client.get(`/houses/${houseId}/alerts/events/`, { params })
  return response.data
}

/**
 * Perform action on an alert event
 * @param {string} houseId 
 * @param {string} eventId 
 * @param {Object} data - {action: 'acknowledge'|'snooze'|'dismiss'|'auto_off', snooze_minutes?: number}
 * @returns {Promise<{message: string, event: Object}>}
 */
export async function alertEventAction(houseId, eventId, data) {
  const response = await client.post(`/houses/${houseId}/alerts/events/${eventId}/action/`, data)
  return response.data
}

/**
 * Trigger alert check (called after energy reading)
 * @param {string} houseId 
 * @param {Object} data - {plug_id: string, power_w: number, session_minutes: number}
 * @returns {Promise<{triggered_count: number, events: Array}>}
 */
export async function triggerAlertCheck(houseId, data) {
  const response = await client.post(`/houses/${houseId}/alerts/trigger/`, data)
  return response.data
}

/**
 * Register push notification token
 * @param {Object} data - {token: string, platform: 'fcm'|'apns', device_label?: string}
 * @returns {Promise<{message: string}>}
 */
export async function registerPushToken(data) {
  const response = await client.post('/alerts/push-token/', data)
  return response.data
}

/**
 * Delete push notification token
 * @param {Object} data - {token: string}
 * @returns {Promise<{message: string}>}
 */
export async function deletePushToken(data) {
  const response = await client.delete('/alerts/push-token/', { data })
  return response.data
}

/**
 * Get user notifications
 * @returns {Promise<Array>}
 */
export async function getUserNotifications() {
  const response = await client.get('/alerts/notifications/')
  return response.data
}
