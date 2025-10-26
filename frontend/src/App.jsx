import { useState, useEffect, useRef } from 'react'
import './App.css'
import LampToggle from './LampToggle'
import EyesTracking from './EyesTracking'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import AuthWrapper from './components/AuthWrapper'
import ChatApp from './components/ChatApp'

const AppContent = () => {
  const { user, isLoading } = useAuth()

  if (isLoading) {
  return (
    <div className="app">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Đang tải...</p>
      </div>
    </div>
    )
  }

  return user ? <ChatApp /> : <AuthWrapper />
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App