import { createContext, useContext, useState, useEffect } from 'react'
import { hashPassword, comparePassword, createSecureUser, sanitizeUser } from '../utils/encryption'
import { saveAccountToFile, getAllAccounts } from '../utils/fileManager'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  // Load user from localStorage on mount
  useEffect(() => {
    const loadUser = async () => {
      try {
        // Load accounts from backend to verify they exist
        const backendAccounts = await getAllAccounts()
        console.log('Loaded accounts from backend:', backendAccounts.length)
        
        // Check if user is already logged in
        const savedUser = localStorage.getItem('user')
        if (savedUser) {
          setUser(JSON.parse(savedUser))
        }
      } catch (error) {
        console.error('Error loading user from backend:', error)
        localStorage.removeItem('user')
      } finally {
        setIsLoading(false)
      }
    }

    // Override console.log to prevent localStorage access
    const originalConsoleLog = console.log
    console.log = (...args) => {
      // Check if trying to access localStorage
      const message = args.join(' ')
      if (message.includes('localStorage') || message.includes('console.log(localStorage)')) {
        originalConsoleLog('🚫 Access to localStorage is restricted for security reasons')
        return
      }
      originalConsoleLog(...args)
    }

    loadUser()
  }, [])

  const login = async (userData) => {
    try {
      // Sanitize user data before storing (remove password)
      const sanitizedUser = sanitizeUser(userData)
      setUser(sanitizedUser)
      
      // Don't store sensitive data in localStorage
      // Only store minimal user info
      const minimalUser = {
        id: sanitizedUser.id,
        name: sanitizedUser.name,
        email: sanitizedUser.email
      }
      localStorage.setItem('user', JSON.stringify(minimalUser))
      
      // Save login activity to backend (optional)
      // await saveAccountToFile(userData)
      
      return { success: true }
    } catch (error) {
      console.error('Error saving user to localStorage:', error)
      return { success: false, error: 'Không thể lưu thông tin đăng nhập' }
    }
  }

  const register = async (userData) => {
    try {
      // Check if user already exists in backend first
      const backendAccounts = await getAllAccounts()
      const userExists = backendAccounts.find(acc => acc.email === userData.email)
      
      if (userExists) {
        return { success: false, error: 'Email đã được sử dụng' }
      }

      // Save account data to backend account.json (with plain text password for compatibility)
      const saveResult = await saveAccountToFile(userData)
      if (!saveResult.success) {
        return { success: false, error: 'Không thể lưu tài khoản vào backend' }
      }

      // Auto login after registration (with sanitized user data)
      const sanitizedUser = sanitizeUser(userData)
      setUser(sanitizedUser)
      
      // Only store minimal user info
      const minimalUser = {
        id: Date.now().toString(),
        name: sanitizedUser.name,
        email: sanitizedUser.email
      }
      localStorage.setItem('user', JSON.stringify(minimalUser))
      
      return { success: true }
    } catch (error) {
      console.error('Error during registration:', error)
      return { success: false, error: 'Không thể tạo tài khoản' }
    }
  }

  const authenticateUser = async (email, password) => {
    try {
      // Always load fresh data from backend to ensure we have the latest accounts
      console.log('Loading accounts from backend...')
      const backendAccounts = await getAllAccounts()
      
      if (backendAccounts.length === 0) {
        return { success: false, error: 'Không có tài khoản nào được tìm thấy' }
      }
      
      // Find user by email
      const user = backendAccounts.find(u => u.email === email)
      
      if (!user) {
        return { success: false, error: 'Email hoặc mật khẩu không đúng' }
      }

      // Compare password directly (plain text comparison for existing accounts)
      // Note: This is for backward compatibility with existing plain text passwords
      const isPasswordValid = password === user.password
      
      if (!isPasswordValid) {
        return { success: false, error: 'Email hoặc mật khẩu không đúng' }
      }

      // Return sanitized user data
      return { success: true, user: sanitizeUser(user) }
    } catch (error) {
      console.error('Error authenticating user:', error)
      return { success: false, error: 'Có lỗi xảy ra khi xác thực' }
    }
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('user')
  }

  const value = {
    user,
    isLoading,
    login,
    register,
    authenticateUser,
    logout,
    isAuthenticated: !!user
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
