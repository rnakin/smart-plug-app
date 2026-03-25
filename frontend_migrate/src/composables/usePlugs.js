/**
 * Plugs composable
 * Handles smart plug data and actions
 */
import { ref, computed } from 'vue'
import * as plugsApi from '../api/plugs'

// Shared state
const plugs = ref([])
const devices = ref([])
const nfcTags = ref([])
const isLoading = ref(false)
const error = ref(null)

export function usePlugs() {
  // Computed
  const hasPlugs = computed(() => plugs.value.length > 0)
  const plugCount = computed(() => plugs.value.length)
  const activePlugs = computed(() => 
    plugs.value.filter(p => p.is_on)
  )
  const inactivePlugs = computed(() => 
    plugs.value.filter(p => !p.is_on)
  )
  const totalPower = computed(() => 
    plugs.value.reduce((sum, p) => sum + (p.current_power_w || 0), 0)
  )

  /**
   * Fetch all plugs for a house
   * @param {string} houseId 
   * @returns {Promise<Array>}
   */
  async function fetchPlugs(houseId) {
    isLoading.value = true
    error.value = null

    try {
      const data = await plugsApi.getPlugs(houseId)
      plugs.value = data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch plugs'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch a single plug
   * @param {string} houseId 
   * @param {string} plugId 
   * @returns {Promise<Object>}
   */
  async function fetchPlug(houseId, plugId) {
    isLoading.value = true
    error.value = null

    try {
      const data = await plugsApi.getPlug(houseId, plugId)
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch plug'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create a new plug
   * @param {string} houseId 
   * @param {Object} data - {name: string, mqtt_topic?: string, nfc_tag_id?: string}
   * @returns {Promise<Object>}
   */
  async function createPlug(houseId, data) {
    isLoading.value = true
    error.value = null

    try {
      const newPlug = await plugsApi.createPlug(houseId, data)
      plugs.value.push(newPlug)
      return newPlug
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to create plug'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update a plug
   * @param {string} houseId 
   * @param {string} plugId 
   * @param {Object} data 
   * @returns {Promise<Object>}
   */
  async function updatePlug(houseId, plugId, data) {
    isLoading.value = true
    error.value = null

    try {
      const updated = await plugsApi.updatePlug(houseId, plugId, data)
      const index = plugs.value.findIndex(p => p.id === plugId)
      if (index !== -1) {
        plugs.value[index] = updated
      }
      return updated
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to update plug'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete a plug
   * @param {string} houseId 
   * @param {string} plugId 
   * @returns {Promise<void>}
   */
  async function deletePlug(houseId, plugId) {
    isLoading.value = true
    error.value = null

    try {
      await plugsApi.deletePlug(houseId, plugId)
      plugs.value = plugs.value.filter(p => p.id !== plugId)
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to delete plug'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Control a plug (turn on/off)
   * @param {string} houseId 
   * @param {string} plugId 
   * @param {string} action - 'on' or 'off'
   * @returns {Promise<Object>}
   */
  async function controlPlug(houseId, plugId, action) {
    isLoading.value = true
    error.value = null

    try {
      const result = await plugsApi.controlPlug(houseId, plugId, { action })
      // Update local state
      const index = plugs.value.findIndex(p => p.id === plugId)
      if (index !== -1) {
        plugs.value[index] = { ...plugs.value[index], is_on: action === 'on' }
      }
      return result
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to control plug'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Toggle a plug
   * @param {string} houseId 
   * @param {string} plugId 
   * @param {boolean} currentState 
   * @returns {Promise<Object>}
   */
  async function togglePlug(houseId, plugId, currentState) {
    const action = currentState ? 'off' : 'on'
    return controlPlug(houseId, plugId, action)
  }

  /**
   * Fetch all devices for a house
   * @param {string} houseId 
   * @returns {Promise<Array>}
   */
  async function fetchDevices(houseId) {
    isLoading.value = true
    error.value = null

    try {
      const data = await plugsApi.getDevices(houseId)
      devices.value = data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch devices'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create a new device
   * @param {string} houseId 
   * @param {Object} data - {name: string, plug_id: string, device_type?: string, power_w?: number}
   * @returns {Promise<Object>}
   */
  async function createDevice(houseId, data) {
    isLoading.value = true
    error.value = null

    try {
      const newDevice = await plugsApi.createDevice(houseId, data)
      devices.value.push(newDevice)
      return newDevice
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to create device'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update a device
   * @param {string} houseId 
   * @param {string} deviceId 
   * @param {Object} data 
   * @returns {Promise<Object>}
   */
  async function updateDevice(houseId, deviceId, data) {
    isLoading.value = true
    error.value = null

    try {
      const updated = await plugsApi.updateDevice(houseId, deviceId, data)
      const index = devices.value.findIndex(d => d.id === deviceId)
      if (index !== -1) {
        devices.value[index] = updated
      }
      return updated
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to update device'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete a device
   * @param {string} houseId 
   * @param {string} deviceId 
   * @returns {Promise<void>}
   */
  async function deleteDevice(houseId, deviceId) {
    isLoading.value = true
    error.value = null

    try {
      await plugsApi.deleteDevice(houseId, deviceId)
      devices.value = devices.value.filter(d => d.id !== deviceId)
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to delete device'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch all NFC tags for a house
   * @param {string} houseId 
   * @returns {Promise<Array>}
   */
  async function fetchNFCTags(houseId) {
    isLoading.value = true
    error.value = null

    try {
      const data = await plugsApi.getNFCTags(houseId)
      nfcTags.value = data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch NFC tags'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Register a new NFC tag
   * @param {string} houseId 
   * @param {Object} data - {tag_id: string, plug_id: string, label?: string}
   * @returns {Promise<Object>}
   */
  async function registerNFCTag(houseId, data) {
    isLoading.value = true
    error.value = null

    try {
      const newTag = await plugsApi.registerNFCTag(houseId, data)
      nfcTags.value.push(newTag)
      return newTag
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to register NFC tag'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update an NFC tag
   * @param {string} houseId 
   * @param {string} tagId 
   * @param {Object} data 
   * @returns {Promise<Object>}
   */
  async function updateNFCTag(houseId, tagId, data) {
    isLoading.value = true
    error.value = null

    try {
      const updated = await plugsApi.updateNFCTag(houseId, tagId, data)
      const index = nfcTags.value.findIndex(t => t.id === tagId)
      if (index !== -1) {
        nfcTags.value[index] = updated
      }
      return updated
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to update NFC tag'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete an NFC tag
   * @param {string} houseId 
   * @param {string} tagId 
   * @returns {Promise<void>}
   */
  async function deleteNFCTag(houseId, tagId) {
    isLoading.value = true
    error.value = null

    try {
      await plugsApi.deleteNFCTag(houseId, tagId)
      nfcTags.value = nfcTags.value.filter(t => t.id !== tagId)
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to delete NFC tag'
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
    plugs.value = []
    devices.value = []
    nfcTags.value = []
    error.value = null
  }

  return {
    // State
    plugs,
    devices,
    nfcTags,
    isLoading,
    error,
    // Computed
    hasPlugs,
    plugCount,
    activePlugs,
    inactivePlugs,
    totalPower,
    // Plug methods
    fetchPlugs,
    fetchPlug,
    createPlug,
    updatePlug,
    deletePlug,
    controlPlug,
    togglePlug,
    // Device methods
    fetchDevices,
    createDevice,
    updateDevice,
    deleteDevice,
    // NFC methods
    fetchNFCTags,
    registerNFCTag,
    updateNFCTag,
    deleteNFCTag,
    // Utility
    clearError,
    reset,
  }
}
