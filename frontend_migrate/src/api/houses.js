/**
 * House API endpoints
 */
import client from './client'

/**
 * Get all houses where user is a member
 * @returns {Promise<Array<{id: string, house_name: string, address: string, lat: number, long: number, role: string, emoji: string, created_at: string}>>}
 */
export async function getHouses() {
  const response = await client.get('/houses/')
  return response.data
}

/**
 * Create a new house
 * @param {Object} data - {house_name: string, address: string, lat?: number, long?: number, emoji?: string}
 * @returns {Promise<{id: string, house_name: string, address: string, lat: number, long: number, emoji: string, role: string, created_at: string}>}
 */
export async function createHouse(data) {
  const response = await client.post('/houses/', data)
  return response.data
}

/**
 * Get house details
 * @param {string} houseId 
 * @returns {Promise<{id: string, house_name: string, address: string, lat: number, long: number, emoji: string, role: string, created_at: string}>}
 */
export async function getHouse(houseId) {
  const response = await client.get(`/houses/${houseId}/`)
  return response.data
}

/**
 * Update house details
 * @param {string} houseId 
 * @param {Object} data - {house_name?: string, address?: string, lat?: number, long?: number, emoji?: string}
 * @returns {Promise<{id: string, house_name: string, address: string, lat: number, long: number, role: string, created_at: string}>}
 */
export async function updateHouse(houseId, data) {
  const response = await client.patch(`/houses/${houseId}/`, data)
  return response.data
}

/**
 * Delete a house
 * @param {string} houseId 
 * @returns {Promise<{message: string}>}
 */
export async function deleteHouse(houseId) {
  const response = await client.delete(`/houses/${houseId}/`)
  return response.data
}

/**
 * Get all members of a house
 * @param {string} houseId 
 * @returns {Promise<Array<{id: string, user_id: string, username: string, email: string, role: string, joined_at: string}>>}
 */
export async function getHouseMembers(houseId) {
  const response = await client.get(`/houses/${houseId}/users/`)
  return response.data
}

/**
 * Invite a user to a house
 * @param {string} houseId 
 * @param {Object} data - {email: string, role?: 'admin'|'member'|'guest'}
 * @returns {Promise<{message: string, user_id: string, email: string, role: string}>}
 */
export async function inviteUser(houseId, data) {
  const response = await client.post(`/houses/${houseId}/users/invite/`, data)
  return response.data
}

/**
 * Manage a house member (remove or update role)
 * @param {string} houseId 
 * @param {Object} data - {action: 'remove'|'update_role', user_id: string, role?: string}
 * @returns {Promise<{message: string}>}
 */
export async function manageMember(houseId, data) {
  const response = await client.post(`/houses/${houseId}/users/manage/`, data)
  return response.data
}

/**
 * Leave a house
 * @param {string} houseId 
 * @returns {Promise<{message: string}>}
 */
export async function leaveHouse(houseId) {
  const response = await client.post(`/houses/${houseId}/leave/`)
  return response.data
}

/**
 * Transfer house ownership
 * @param {string} houseId 
 * @param {Object} data - {new_owner_id: string}
 * @returns {Promise<{message: string}>}
 */
export async function transferOwnership(houseId, data) {
  const response = await client.post(`/houses/${houseId}/transfer/`, data)
  return response.data
}
