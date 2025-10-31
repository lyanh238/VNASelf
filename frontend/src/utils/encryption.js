import bcrypt from 'bcryptjs'

// Salt rounds for bcrypt (higher = more secure but slower)
const SALT_ROUNDS = 12

/**
 * Hash a password using bcrypt
 * @param {string} password - Plain text password
 * @returns {Promise<string>} - Hashed password
 */
export const hashPassword = async (password) => {
  try {
    const hashedPassword = await bcrypt.hash(password, SALT_ROUNDS)
    return hashedPassword
  } catch (error) {
    console.error('Error hashing password:', error)
    throw new Error('Không thể mã hóa mật khẩu')
  }
}

/**
 * Compare a plain text password with a hashed password
 * @param {string} password - Plain text password
 * @param {string} hashedPassword - Hashed password from storage
 * @returns {Promise<boolean>} - True if passwords match
 */
export const comparePassword = async (password, hashedPassword) => {
  try {
    const isMatch = await bcrypt.compare(password, hashedPassword)
    return isMatch
  } catch (error) {
    console.error('Error comparing password:', error)
    return false
  }
}

/**
 * Encrypt sensitive data using a simple encryption
 * @param {string} data - Data to encrypt
 * @returns {string} - Encrypted data
 */
export const encryptData = (data) => {
  try {
    // Simple base64 encoding with a prefix to identify encrypted data
    const encrypted = btoa(encodeURIComponent(data))
    return `encrypted_${encrypted}`
  } catch (error) {
    console.error('Error encrypting data:', error)
    return data
  }
}

/**
 * Decrypt sensitive data
 * @param {string} encryptedData - Encrypted data
 * @returns {string} - Decrypted data
 */
export const decryptData = (encryptedData) => {
  try {
    if (encryptedData.startsWith('encrypted_')) {
      const data = encryptedData.replace('encrypted_', '')
      return decodeURIComponent(atob(data))
    }
    return encryptedData
  } catch (error) {
    console.error('Error decrypting data:', error)
    return encryptedData
  }
}

/**
 * Create a secure user object for storage
 * @param {Object} userData - User data with plain text password
 * @returns {Promise<Object>} - User object with hashed password
 */
export const createSecureUser = async (userData) => {
  const { password, ...otherData } = userData
  const hashedPassword = await hashPassword(password)
  
  return {
    ...otherData,
    password: hashedPassword,
    createdAt: new Date().toISOString(),
    id: Date.now().toString()
  }
}

/**
 * Sanitize user data for display (remove sensitive info)
 * @param {Object} user - User object
 * @returns {Object} - Sanitized user object
 */
export const sanitizeUser = (user) => {
  const { password, ...sanitizedUser } = user
  return sanitizedUser
}
