/**
 * File Manager - Saves account data to backend account.json file
 * This will send data to backend API to save in account.json on server
 */

/**
 * Save account data to backend account.json file
 * @param {Object} accountData - Account data to save
 */
export const saveAccountToFile = async (accountData) => {
  try {
    // Prepare account data for backend
    const accountPayload = {
      name: accountData.name,
      email: accountData.email,
      password: accountData.password,
      created_at: accountData.createdAt || new Date().toISOString()
    }
    
    // Send to backend API
    const response = await fetch('/api/accounts/save', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(accountPayload)
    })
    
    if (response.ok) {
      const result = await response.json()
      console.log('Account data saved to backend account.json:', result.message)
      return { success: true, message: result.message }
    } else {
      const error = await response.json()
      console.error('Error saving account to backend:', error.detail)
      return { success: false, error: error.detail }
    }
  } catch (error) {
    console.error('Error saving account to backend:', error)
    return { success: false, error: 'Failed to connect to backend' }
  }
}

/**
 * Get all accounts from backend
 * @returns {Promise<Array>} - Array of account objects
 */
export const getAllAccounts = async () => {
  try {
    const response = await fetch('/api/accounts')
    if (response.ok) {
      const result = await response.json()
      return result.accounts || []
    } else {
      console.error('Error getting accounts from backend')
      return []
    }
  } catch (error) {
    console.error('Error getting accounts from backend:', error)
    return []
  }
}

/**
 * Get account by email from backend
 * @param {string} email - Email to search for
 * @returns {Promise<Object|null>} - Account object or null
 */
export const getAccountByEmail = async (email) => {
  try {
    const response = await fetch(`/api/accounts/${encodeURIComponent(email)}`)
    if (response.ok) {
      const result = await response.json()
      return result.account
    } else if (response.status === 404) {
      return null
    } else {
      console.error('Error getting account from backend')
      return null
    }
  } catch (error) {
    console.error('Error getting account from backend:', error)
    return null
  }
}

/**
 * Delete account by email from backend
 * @param {string} email - Email of account to delete
 * @returns {Promise<boolean>} - Success status
 */
export const deleteAccount = async (email) => {
  try {
    const response = await fetch(`/api/accounts/${encodeURIComponent(email)}`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      const result = await response.json()
      console.log('Account deleted from backend:', result.message)
      return true
    } else {
      console.error('Error deleting account from backend')
      return false
    }
  } catch (error) {
    console.error('Error deleting account from backend:', error)
    return false
  }
}
