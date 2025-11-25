import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import './Auth.css'

const Login = ({ onSwitchToRegister }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { authenticateUser, login } = useAuth()

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    // Clear error when user starts typing
    if (error) setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    // Basic validation
    if (!formData.email || !formData.password) {
      setError('Vui lòng điền đầy đủ thông tin')
      setIsLoading(false)
      return
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) {
      setError('Email không hợp lệ')
      setIsLoading(false)
      return
    }

    try {
      // Authenticate user with bcrypt
      const authResult = await authenticateUser(formData.email, formData.password)
      
      if (authResult.success) {
        const loginResult = await login(authResult.user)
        
        if (loginResult.success) {
          // Login successful, component will be unmounted by parent
        } else {
          setError(loginResult.error)
        }
      } else {
        setError(authResult.error)
      }
    } catch (error) {
      console.error('Login error:', error)
      setError('Có lỗi xảy ra khi đăng nhập')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">
            <img src="/src/assets/qai_gen.png" alt="X23D8" />
          </div>
          <h1>Chào mừng trở lại</h1>
          <p>Đăng nhập để tiếp tục sử dụng X23D8</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Nhập email của bạn"
              required
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Mật khẩu</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Nhập mật khẩu"
              required
              disabled={isLoading}
            />
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button 
            type="submit" 
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Chưa có tài khoản?{' '}
            <button 
              type="button" 
              className="auth-link"
              onClick={onSwitchToRegister}
              disabled={isLoading}
            >
              Đăng ký ngay
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login
