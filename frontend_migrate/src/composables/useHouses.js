/**
 * Houses composable
 * Handles house data and actions
 */
import { ref, computed } from 'vue'
import * as housesApi from '../api/houses'

// Shared state
const houses = ref([])
const currentHouse = ref(null)
const houseMembers = ref([])
const isLoading = ref(false)
const error = ref(null)

export function useHouses() {
  // Computed
  const hasHouses = computed(() => houses.value.length > 0)
  const houseCount = computed(() => houses.value.length)
  const ownedHouses = computed(() => 
    houses.value.filter(h => h.user_role === 'owner')
  )
  const memberHouses = computed(() => 
    houses.value.filter(h => h.user_role === 'member')
  )

  /**
   * Fetch all houses for current user
   * @returns {Promise<void>}
   */
  async function fetchHouses() {
    isLoading.value = true
    error.value = null

    try {
      const data = await housesApi.getHouses()
      houses.value = data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch houses'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch a single house
   * @param {string} houseId 
   * @returns {Promise<Object>}
   */
  async function fetchHouse(houseId) {
    isLoading.value = true
    error.value = null

    try {
      const data = await housesApi.getHouse(houseId)
      currentHouse.value = data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch house'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create a new house
   * @param {Object} data - {name: string, address?: string, emoji?: string}
   * @returns {Promise<Object>}
   */
  async function createHouse(data) {
    isLoading.value = true
    error.value = null

    try {
      const newHouse = await housesApi.createHouse(data)
      houses.value.push(newHouse)
      return newHouse
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to create house'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update a house
   * @param {string} houseId 
   * @param {Object} data 
   * @returns {Promise<Object>}
   */
  async function updateHouse(houseId, data) {
    isLoading.value = true
    error.value = null

    try {
      const updated = await housesApi.updateHouse(houseId, data)
      const index = houses.value.findIndex(h => h.id === houseId)
      if (index !== -1) {
        houses.value[index] = updated
      }
      if (currentHouse.value?.id === houseId) {
        currentHouse.value = updated
      }
      return updated
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to update house'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete a house
   * @param {string} houseId 
   * @returns {Promise<void>}
   */
  async function deleteHouse(houseId) {
    isLoading.value = true
    error.value = null

    try {
      await housesApi.deleteHouse(houseId)
      houses.value = houses.value.filter(h => h.id !== houseId)
      if (currentHouse.value?.id === houseId) {
        currentHouse.value = null
      }
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to delete house'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch members of a house
   * @param {string} houseId 
   * @returns {Promise<Array>}
   */
  async function fetchMembers(houseId) {
    isLoading.value = true
    error.value = null

    try {
      const data = await housesApi.getHouseMembers(houseId)
      houseMembers.value = data
      return data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch members'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Invite a user to a house
   * @param {string} houseId 
   * @param {Object} data - {email: string, role?: 'owner'|'member'}
   * @returns {Promise<Object>}
   */
  async function inviteUser(houseId, data) {
    isLoading.value = true
    error.value = null

    try {
      const result = await housesApi.inviteUser(houseId, data)
      return result
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to invite user'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Manage a member (change role or remove)
   * @param {string} houseId 
   * @param {string} memberId 
   * @param {Object} data - {action: 'remove'|'set_role', role?: 'owner'|'member'}
   * @returns {Promise<Object>}
   */
  async function manageMember(houseId, memberId, data) {
    isLoading.value = true
    error.value = null

    try {
      const result = await housesApi.manageMember(houseId, memberId, data)
      // Refresh members list
      await fetchMembers(houseId)
      return result
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to manage member'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Leave a house
   * @param {string} houseId 
   * @returns {Promise<void>}
   */
  async function leaveHouse(houseId) {
    isLoading.value = true
    error.value = null

    try {
      await housesApi.leaveHouse(houseId)
      houses.value = houses.value.filter(h => h.id !== houseId)
      if (currentHouse.value?.id === houseId) {
        currentHouse.value = null
      }
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to leave house'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Transfer house ownership
   * @param {string} houseId 
   * @param {string} newOwnerId 
   * @returns {Promise<Object>}
   */
  async function transferOwnership(houseId, newOwnerId) {
    isLoading.value = true
    error.value = null

    try {
      const result = await housesApi.transferOwnership(houseId, newOwnerId)
      // Refresh houses to update roles
      await fetchHouses()
      return result
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to transfer ownership'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Set current house
   * @param {Object} house 
   */
  function setCurrentHouse(house) {
    currentHouse.value = house
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
    houses.value = []
    currentHouse.value = null
    houseMembers.value = []
    error.value = null
  }

  return {
    // State
    houses,
    currentHouse,
    houseMembers,
    isLoading,
    error,
    // Computed
    hasHouses,
    houseCount,
    ownedHouses,
    memberHouses,
    // Methods
    fetchHouses,
    fetchHouse,
    createHouse,
    updateHouse,
    deleteHouse,
    fetchMembers,
    inviteUser,
    manageMember,
    leaveHouse,
    transferOwnership,
    setCurrentHouse,
    clearError,
    reset,
  }
}
