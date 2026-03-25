/**
 * Smart Plug API endpoints
 */
import client from './client'

/**
 * Get all plugs in a house
 * @param {string} houseId 
 * @returns {Promise<Array<{id: string, house_id: string, plug_code: string, name: string, location: string, is_on: boolean, online_status: string, registered_at: string, current_power_w: number, device_id: string, device_name: string, device_type: string, device_emoji: string, device_risk: string}>>}
 */
export async function getPlugs(houseId) {
  const response = await client.get(`/houses/${houseId}/plugs/`)
  return response.data
}

/**
 * Register a new plug
 * @param {string} houseId 
 * @param {Object} data - {plug_code: string, name: string, location?: string}
 * @returns {Promise<{id: string, house_id: string, plug_code: string, name: string, location: string, is_on: boolean, online_status: string, registered_at: string}>}
 */
export async function createPlug(houseId, data) {
  const response = await client.post(`/houses/${houseId}/plugs/`, data)
  return response.data
}

/**
 * Get plug details
 * @param {string} houseId 
 * @param {string} plugId 
 * @returns {Promise<{id: string, house_id: string, plug_code: string, name: string, location: string, is_on: boolean, online_status: string, registered_at: string, current_power_w: number, device_id: string, device_name: string, device_type: string, device_emoji: string, device_risk: string}>}
 */
export async function getPlug(houseId, plugId) {
  const response = await client.get(`/houses/${houseId}/plugs/${plugId}/`)
  return response.data
}

/**
 * Update plug details
 * @param {string} houseId 
 * @param {string} plugId 
 * @param {Object} data - {name?: string, location?: string}
 * @returns {Promise<{id: string, house_id: string, plug_code: string, name: string, location: string, is_on: boolean, online_status: string, registered_at: string}>}
 */
export async function updatePlug(houseId, plugId, data) {
  const response = await client.patch(`/houses/${houseId}/plugs/${plugId}/`, data)
  return response.data
}

/**
 * Delete a plug
 * @param {string} houseId 
 * @param {string} plugId 
 * @returns {Promise<{message: string}>}
 */
export async function deletePlug(houseId, plugId) {
  const response = await client.delete(`/houses/${houseId}/plugs/${plugId}/`)
  return response.data
}

/**
 * Control a plug (turn on/off)
 * @param {string} houseId 
 * @param {string} plugId 
 * @param {Object} data - {action: 'on'|'off'}
 * @returns {Promise<{id: string, is_on: boolean}>}
 */
export async function controlPlug(houseId, plugId, data) {
  const response = await client.post(`/houses/${houseId}/plugs/${plugId}/control/`, data)
  return response.data
}

/**
 * Get all electrical devices in a house
 * @param {string} houseId 
 * @returns {Promise<Array<{id: string, house_id: string, name: string, device_type: string, rated_power_watts: number, risk_level: string, auto_cutoff_minutes: number, created_at: string}>>}
 */
export async function getDevices(houseId) {
  const response = await client.get(`/houses/${houseId}/devices/`)
  return response.data
}

/**
 * Create an electrical device
 * @param {string} houseId 
 * @param {Object} data - {name: string, device_type?: string, rated_power_watts: number, risk_level?: string, auto_cutoff_minutes?: number}
 * @returns {Promise<{id: string, house_id: string, name: string, device_type: string, rated_power_watts: number, risk_level: string, auto_cutoff_minutes: number, created_at: string}>}
 */
export async function createDevice(houseId, data) {
  const response = await client.post(`/houses/${houseId}/devices/`, data)
  return response.data
}

/**
 * Get device details
 * @param {string} houseId 
 * @param {string} deviceId 
 * @returns {Promise<{id: string, house_id: string, name: string, device_type: string, rated_power_watts: number, risk_level: string, auto_cutoff_minutes: number, created_at: string}>}
 */
export async function getDevice(houseId, deviceId) {
  const response = await client.get(`/houses/${houseId}/devices/${deviceId}/`)
  return response.data
}

/**
 * Update device details
 * @param {string} houseId 
 * @param {string} deviceId 
 * @param {Object} data - {name?: string, device_type?: string, rated_power_watts?: number, risk_level?: string, auto_cutoff_minutes?: number}
 * @returns {Promise<{id: string, house_id: string, name: string, device_type: string, rated_power_watts: number, risk_level: string, auto_cutoff_minutes: number, created_at: string}>}
 */
export async function updateDevice(houseId, deviceId, data) {
  const response = await client.patch(`/houses/${houseId}/devices/${deviceId}/`, data)
  return response.data
}

/**
 * Delete a device
 * @param {string} houseId 
 * @param {string} deviceId 
 * @returns {Promise<{message: string}>}
 */
export async function deleteDevice(houseId, deviceId) {
  const response = await client.delete(`/houses/${houseId}/devices/${deviceId}/`)
  return response.data
}

/**
 * Get all NFC tags in a house
 * @param {string} houseId 
 * @returns {Promise<Array<{id: string, tag_uid: string, device_id: string, device_name: string, label: string, registered_at: string}>>}
 */
export async function getNFCTags(houseId) {
  const response = await client.get(`/houses/${houseId}/nfc/`)
  return response.data
}

/**
 * Register an NFC tag
 * @param {string} houseId 
 * @param {Object} data - {tag_uid: string, device_id?: string, label?: string}
 * @returns {Promise<{id: string, tag_uid: string, device_id: string, device_name: string, label: string, registered_at: string}>}
 */
export async function registerNFCTag(houseId, data) {
  const response = await client.post(`/houses/${houseId}/nfc/register/`, data)
  return response.data
}

/**
 * Get NFC tag details
 * @param {string} houseId 
 * @param {string} tagId 
 * @returns {Promise<{id: string, tag_uid: string, device_id: string, device_name: string, label: string, registered_at: string}>}
 */
export async function getNFCTag(houseId, tagId) {
  const response = await client.get(`/houses/${houseId}/nfc/${tagId}/`)
  return response.data
}

/**
 * Update NFC tag
 * @param {string} houseId 
 * @param {string} tagId 
 * @param {Object} data - {label?: string, device_id?: string}
 * @returns {Promise<{id: string, tag_uid: string, device_id: string, device_name: string, label: string, registered_at: string}>}
 */
export async function updateNFCTag(houseId, tagId, data) {
  const response = await client.patch(`/houses/${houseId}/nfc/${tagId}/`, data)
  return response.data
}

/**
 * Delete an NFC tag
 * @param {string} houseId 
 * @param {string} tagId 
 * @returns {Promise<{message: string}>}
 */
export async function deleteNFCTag(houseId, tagId) {
  const response = await client.delete(`/houses/${houseId}/nfc/${tagId}/`)
  return response.data
}
