/**
 * Energy composable
 * Handles energy data and statistics
 */
import { ref, computed } from 'vue'
import * as energyApi from '../api/energy'

// Shared state
const realtimeData = ref(null)
const energySummary = ref(null)
const dashboardData = ref(null)
const deviceEnergy = ref([])
const plugEnergy = ref([])
const energyReadings = ref([])
const isLoading = ref(false)
const error = ref(null)

export function useEnergy() {
  // Computed
  const currentPower = computed(() => realtimeData.value?.total_power_w || 0)
  const todayEnergy = computed(() => energySummary.value?.today_kwh || 0)
  const monthEnergy = computed(() => energySummary.value?.month_kwh || 0)
  const estimatedCost = computed(() => energySummary.value?.estimated_cost || 0)

  /**
   * Fetch realtime energy data for a house
   * @param {string} houseId 
   * @returns {Promise<Object>}
   */
  async function fetchRealtime(houseId) {
    isLoading.value = true
    error.value = null

    try {
      const data = await energyApi.getRealtimeEnergy(houseId)
      realtimeData.value = data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch realtime data'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch energy summary for a house
   * @param {string} houseId 
   * @param {Object} params - {period?: 'day'|'week'|'month'|'year'}
   * @returns {Promise<Object>}
   */
  async function fetchSummary(houseId, params = {}) {
    isLoading.value = true
    error.value = null

    try {
      const data = await energyApi.getEnergySummary(houseId, params)
      energySummary.value = data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch energy summary'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch dashboard data (aggregated stats)
   * @param {string} houseId 
   * @returns {Promise<Object>}
   */
  async function fetchDashboard(houseId) {
    isLoading.value = true
    error.value = null

    try {
      const data = await energyApi.getEnergyDashboard(houseId)
      dashboardData.value = data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch dashboard data'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch energy by device
   * @param {string} houseId 
   * @param {Object} params - {start_date?: string, end_date?: string}
   * @returns {Promise<Array>}
   */
  async function fetchByDevice(houseId, params = {}) {
    isLoading.value = true
    error.value = null

    try {
      const data = await energyApi.getEnergyByDevice(houseId, params)
      deviceEnergy.value = data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch device energy'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch energy by plug
   * @param {string} houseId 
   * @param {Object} params - {start_date?: string, end_date?: string}
   * @returns {Promise<Array>}
   */
  async function fetchByPlug(houseId, params = {}) {
    isLoading.value = true
    error.value = null

    try {
      const data = await energyApi.getEnergyByPlug(houseId, params)
      plugEnergy.value = data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch plug energy'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch energy readings (time series)
   * @param {string} houseId 
   * @param {Object} params - {plug_id?: string, device_id?: string, start_time?: string, end_time?: string, resolution?: '1m'|'5m'|'1h'|'1d'}
   * @returns {Promise<Object>}
   */
  async function fetchReadings(houseId, params = {}) {
    isLoading.value = true
    error.value = null

    try {
      const data = await energyApi.getEnergyReadings(houseId, params)
      energyReadings.value = data.results || data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch energy readings'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Export energy data
   * @param {string} houseId 
   * @param {Object} params - {format?: 'csv'|'json', start_date?: string, end_date?: string}
   * @returns {Promise<Blob>}
   */
  async function exportData(houseId, params = {}) {
    isLoading.value = true
    error.value = null

    try {
      const blob = await energyApi.exportEnergyData(houseId, params)
      return blob
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to export data'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Submit an energy reading (for testing/manual entry)
   * @param {string} houseId 
   * @param {Object} data - {plug_id: string, power_w: number, session_minutes?: number}
   * @returns {Promise<Object>}
   */
  async function submitReading(houseId, data) {
    isLoading.value = true
    error.value = null

    try {
      const result = await energyApi.ingestEnergyReading(houseId, data)
      return result
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to submit reading'
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
    realtimeData.value = null
    energySummary.value = null
    dashboardData.value = null
    deviceEnergy.value = []
    plugEnergy.value = []
    energyReadings.value = []
    error.value = null
  }

  return {
    // State
    realtimeData,
    energySummary,
    dashboardData,
    deviceEnergy,
    plugEnergy,
    energyReadings,
    isLoading,
    error,
    // Computed
    currentPower,
    todayEnergy,
    monthEnergy,
    estimatedCost,
    // Methods
    fetchRealtime,
    fetchSummary,
    fetchDashboard,
    fetchByDevice,
    fetchByPlug,
    fetchReadings,
    exportData,
    submitReading,
    clearError,
    reset,
  }
}
