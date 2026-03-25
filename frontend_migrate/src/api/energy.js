/**
 * Energy API endpoints
 */
import client from './client'

/**
 * Get real-time energy readings for all plugs in a house
 * @param {string} houseId 
 * @param {string} plugId - optional filter by plug
 * @returns {Promise<Array<{plug_id: string, plug_name: string, location: string, is_on: boolean, online_status: string, latest_reading: {voltage_v: number, current_a: number, power_w: number, energy_kwh: number, recorded_at: string}}>>}
 */
export async function getRealtimeEnergy(houseId, plugId = null) {
  const params = plugId ? { plug_id: plugId } : {}
  const response = await client.get(`/houses/${houseId}/energy/realtime/`, { params })
  return response.data
}

/**
 * Get energy summary
 * @param {string} houseId 
 * @param {Object} params - {period?: 'daily'|'weekly'|'monthly', start?: string, end?: string, plug_id?: string}
 * @returns {Promise<Array<{period: string, total_kwh: number, avg_power_w: number, peak_power_w: number, reading_count: number}>>}
 */
export async function getEnergySummary(houseId, params = {}) {
  const response = await client.get(`/houses/${houseId}/energy/summary/`, { params })
  return response.data
}

/**
 * Get energy dashboard data
 * @param {string} houseId 
 * @param {Object} params - {start?: string, end?: string}
 * @returns {Promise<{total_kwh: number, avg_power_w: number, peak_power_w: number, by_plug: Array, by_device: Array}>}
 */
export async function getEnergyDashboard(houseId, params = {}) {
  const response = await client.get(`/houses/${houseId}/energy/dashboard/`, { params })
  return response.data
}

/**
 * Get energy consumption by device
 * @param {string} houseId 
 * @param {Object} params - {start?: string, end?: string}
 * @returns {Promise<Array<{device_id: string, device_name: string, total_kwh: number, avg_power_w: number}>>}
 */
export async function getEnergyByDevice(houseId, params = {}) {
  const response = await client.get(`/houses/${houseId}/energy/by-device/`, { params })
  return response.data
}

/**
 * Get energy consumption by plug
 * @param {string} houseId 
 * @param {Object} params - {start?: string, end?: string}
 * @returns {Promise<Array<{plug_id: string, plug_name: string, total_kwh: number, avg_power_w: number}>>}
 */
export async function getEnergyByPlug(houseId, params = {}) {
  const response = await client.get(`/houses/${houseId}/energy/by-plug/`, { params })
  return response.data
}

/**
 * Get raw energy readings (paginated)
 * @param {string} houseId 
 * @param {Object} params - {plug_id?: string, start?: string, end?: string, limit?: number, offset?: number}
 * @returns {Promise<{total: number, limit: number, offset: number, results: Array}>}
 */
export async function getEnergyReadings(houseId, params = {}) {
  const response = await client.get(`/houses/${houseId}/energy/readings/`, { params })
  return response.data
}

/**
 * Export energy data as CSV
 * @param {string} houseId 
 * @param {Object} params - {start?: string, end?: string, plug_id?: string}
 * @returns {Promise<Blob>}
 */
export async function exportEnergyData(houseId, params = {}) {
  const response = await client.get(`/houses/${houseId}/energy/export/`, {
    params,
    responseType: 'blob'
  })
  return response.data
}

/**
 * Ingest energy reading (called by plug firmware)
 * @param {string} houseId 
 * @param {Object} data - {plug_id: string, voltage_v: number, current_a: number, power_w: number, energy_kwh?: number, recorded_at?: string}
 * @returns {Promise<{id: string, plug_id: string, power_w: number, recorded_at: string}>}
 */
export async function ingestEnergyReading(houseId, data) {
  const response = await client.post(`/houses/${houseId}/energy/ingest/`, data)
  return response.data
}
