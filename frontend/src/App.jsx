import { useState, useEffect, useRef } from 'react'
import './App.css'
import LampToggle from './LampToggle'
import EyesTracking from './EyesTracking'

function App() {
  const [inputValue, setInputValue] = useState('')
  const [selectedModel, setSelectedModel] = useState('Sonnet 4.5')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [isDarkMode, setIsDarkMode] = useState(true)
  const [greeting, setGreeting] = useState('')
  const [isGreetingChanging, setIsGreetingChanging] = useState(false)
  const [currentThreadId, setCurrentThreadId] = useState(null)
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [showWelcome, setShowWelcome] = useState(true)
  const inputRef = useRef(null)
  const messagesEndRef = useRef(null)

  // Load theme preference from localStorage on component mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark')
    }
  }, [])

  // Save theme preference to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light')
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light')
  }, [isDarkMode])

  // Generate greeting based on current time
  useEffect(() => {
    const getGreeting = () => {
      const now = new Date()
      const hour = now.getHours()
      
      // Array of greetings for each time period
      const morningGreetings = [
        'Good morning',
        'Rise and shine',
        'Morning sunshine',
        'Good morning',
        'Hello there'
      ]
      
      const afternoonGreetings = [
        'Good afternoon',
        'Hello there',
        'Good day',
        'Afternoon',
        'Hey there'
      ]
      
      const eveningGreetings = [
        'Good evening',
        'Evening',
        'Hello',
        'Good evening',
        'Hey'
      ]
      
      const nightGreetings = [
        'Good night',
        'Late night',
        'Still up?',
        'Good night',
        'Night owl'
      ]
      
      // Select random greeting based on time
      let greetings
      if (hour >= 5 && hour < 12) {
        greetings = morningGreetings
      } else if (hour >= 12 && hour < 17) {
        greetings = afternoonGreetings
      } else if (hour >= 17 && hour < 21) {
        greetings = eveningGreetings
      } else {
        greetings = nightGreetings
      }
      
      return greetings[Math.floor(Math.random() * greetings.length)]
    }
    
    setGreeting(getGreeting())
    
    // Update greeting every 5 minutes to handle transitions and add variety
    const interval = setInterval(() => {
      setIsGreetingChanging(true)
      setTimeout(() => {
        setGreeting(getGreeting())
        setTimeout(() => setIsGreetingChanging(false), 100)
      }, 400)
    }, 300000) // Update every 5 minutes
    
    return () => clearInterval(interval)
  }, [])

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode)
  }

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }

  const scrollToBottomImmediate = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "auto" })
    }
  }

  useEffect(() => {
    // Always scroll to bottom when messages change
    const timer = setTimeout(() => {
      scrollToBottom()
    }, 50)
    return () => clearTimeout(timer)
  }, [messages])

  // Force scroll to bottom when new messages are added
  useEffect(() => {
    if (messages.length > 0) {
      const timer = setTimeout(() => {
        scrollToBottomImmediate()
      }, 10)
      return () => clearTimeout(timer)
    }
  }, [messages.length])

  const loadChatHistory = async (threadId) => {
    try {
      const response = await fetch(`/api/chat/history/${threadId}`)
      if (response.ok) {
        const data = await response.json()
        setMessages(data.messages || [])
      }
    } catch (error) {
      console.error('Error loading chat history:', error)
    }
  }

  const sendMessage = async (content) => {
    if (!content.trim()) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    }

    // Add user message immediately
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setShowWelcome(false)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: content.trim(),
          thread_id: currentThreadId,
          user_id: 'default_user'
        })
      })

      if (response.ok) {
        const data = await response.json()
        
        // Update thread ID if this is a new conversation
        if (!currentThreadId) {
          setCurrentThreadId(data.thread_id)
        }

        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: data.content,
          agent_name: data.agent_name,
          timestamp: new Date(data.timestamp).toISOString()
        }

        // Add assistant message
        setMessages(prev => [...prev, assistantMessage])
      } else {
        // Handle different HTTP status codes
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`
        
        if (response.status === 404) {
          errorMessage = "Backend server is not running. Please start the backend with: python backend_api.py"
        } else if (response.status === 500) {
          errorMessage = "Server error. Please check if the multi-agent system is properly initialized."
        } else if (response.status === 422) {
          errorMessage = "Invalid request format. Please try again."
        }
        
        throw new Error(errorMessage)
      }
    } catch (error) {
      console.error('Error sending message:', error)
      
      let userFriendlyMessage = "Xin lỗi, đã có lỗi xảy ra khi xử lý yêu cầu của bạn."
      
      if (error.message.includes('404')) {
        userFriendlyMessage = "Backend server không chạy. Vui lòng khởi động backend với: python backend_api.py"
      } else if (error.message.includes('500')) {
        userFriendlyMessage = "Lỗi server. Vui lòng kiểm tra hệ thống multi-agent đã được khởi tạo đúng chưa."
      } else if (error.message.includes('Failed to fetch')) {
        userFriendlyMessage = "Không thể kết nối đến backend server. Vui lòng đảm bảo nó đang chạy trên port 8000."
      } else if (error.message.includes('body stream already read')) {
        userFriendlyMessage = "Lỗi xử lý response. Vui lòng thử lại."
      } else {
        userFriendlyMessage = `Lỗi: ${error.message}`
      }
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: userFriendlyMessage,
        agent_name: 'Error',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendMessage = async () => {
    if (inputValue.trim()) {
      sendMessage(inputValue)
      setInputValue('')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handlePromptClick = (prompt) => {
    setInputValue(prompt)
    sendMessage(prompt)
    setInputValue('')
  }

  const handleNewChat = () => {
    setCurrentThreadId(null)
    setMessages([])
    setShowWelcome(true)
    setInputValue('')
  }

  // Ensure input stays at bottom when typing
  const handleInputChange = (e) => {
    setInputValue(e.target.value)
    // Scroll to bottom when user is typing
    setTimeout(() => {
      scrollToBottomImmediate()
    }, 10)
  }

  const formatMessage = (content) => {
    // Simple markdown-like formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>')
  }

  return (
    <div className="app">
      {/* Top Bar */}
      <div className="top-bar">
        <div className="top-bar-center">
          <span>X2D35 — Control+Alt+Space</span>
        </div>
        <div className="top-bar-right">
          <LampToggle 
            isDarkMode={isDarkMode}
            onToggle={toggleTheme}
          />
        </div>
      </div>
      <div className="main-container">
        {/* Sidebar */}
        <div className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
          <div className="sidebar-header">
            <button 
              className="hamburger-menu"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            >
              ☰
            </button>
            <div className="X2D35-logo">
              <img src="/src/assets/qai_gen.png" alt="QAI Logo" style={{ width: '150%', height: '150%', objectFit: 'contain' }} />
            </div>
            <span className="X2D35-text">X2D35</span>
          </div>

          <button className="new-chat-btn" onClick={handleNewChat}>
            <span style={{ fontSize: '18px' }}>+</span>
            <span className="new-chat-text">New chat</span>
          </button>

          <nav className="navigation">
            <a href="#" className="nav-link">
              <span className="nav-icon">💬</span>
              Chats
            </a>
            <a href="#" className="nav-link">
              <span className="nav-icon">📁</span>
              Agent
            </a>
          </nav>

          <div className="recents-section">
            <div className="recents-group">
              <h3>Today</h3>
              <div className="recent-item">Medical checkup scheduling</div>
              <div className="recent-item">Two-month sprint planning strat...</div>
              <div className="recent-item">Scheduling plans</div>
              <div className="recent-item">MCP adapter technology</div>
            </div>
            
            <div className="recents-group">
              <h3>Yesterday</h3>
              <div className="recent-item">Medical appointment at Thu Duc...</div>
              <div className="recent-item">Doctor appointment scheduling</div>
              <div className="recent-item">NWS weather alerts and forecas...</div>
              <div className="recent-item">Today's meeting schedule</div>
            </div>

            <div className="recents-group">
              <h3>Previous 7 Days</h3>
              <div className="recent-item">New York weather alerts</div>
              <div className="recent-item">Running X2D35 locally</div>
            </div>
          </div>

          <div className="user-profile">
            <button className="user-profile-btn">
              <div className="user-avatar">L</div>
              <div className="user-info">
                <div className="user-name">Lee</div>
                {/* <div className="user-plan">Free plan</div> */}
              </div>
              <div className="user-dropdown">▼</div>
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="main-content">
          {showWelcome && messages.length === 0 ? (
            <>
              <div className="welcome-section">
                <div className="X2D35-icon-large">
                  <EyesTracking inputRef={inputRef} />
                </div>
                <h1 className={`welcome-text ${isGreetingChanging ? 'greeting-change' : ''}`}>
                  {greeting}, Lee
                </h1>
              </div>

              <div className="chat-input-container">
                <div className="chat-input">
                  <div className="input-controls-left">
                    <button className="input-btn">+</button>
                  </div>
                  <input
                    ref={inputRef}
                    type="text"
                    placeholder="How can I help you today?"
                    value={inputValue}
                    onChange={handleInputChange}
                    onKeyPress={handleKeyPress}
                    className="chat-input-field"
                  />
                  <div className="input-controls-right">
                    <select 
                      value={selectedModel} 
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="model-select"
                    >
                      <option value="Sonnet 4.5">Sonnet 4.5</option>
                      <option value="Opus">Opus</option>
                      <option value="Haiku">Haiku</option>
                    </select>
                    <button 
                      className="send-btn" 
                      onClick={handleSendMessage}
                      disabled={!inputValue.trim()}
                    >
                      →
                    </button>
                  </div>
                </div>
              </div>

              <div className="prompt-suggestions">
                <button 
                  className="prompt-btn"
                  onClick={() => handlePromptClick('Schedule a medical appointment')}
                >
                  <span>📅</span>
                  <span>Schedule Appointment</span>
                </button>
                <button 
                  className="prompt-btn"
                  onClick={() => handlePromptClick('Check available time slots')}
                >
                  <span>📋</span>
                  <span>Check Schedule</span>
                </button>
                <button 
                  className="prompt-btn"
                  onClick={() => handlePromptClick('Get health advice')}
                >
                  <span>🏥</span>
                  <span>Health Advice</span>
                </button>
                <button 
                  className="prompt-btn"
                  onClick={() => handlePromptClick('Monitor blood pressure')}
                >
                  <span>💊</span>
                  <span>Blood Pressure</span>
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Chat Messages */}
              <div className="chat-messages">
                {messages.map((message) => (
                  <div key={message.id} className={`message ${message.type}`}>
                    <div className="message-avatar">
                      {message.type === 'user' ? 'U' : (
                        <img src="/src/assets/qai_gen.png" alt="QAI" style={{ width: '150%', height: '150%', objectFit: 'contain', borderRadius: '50%' }} />
                      )}
                    </div>
                    <div className="message-content">
                      <div className="message-header">
                        <span className="message-role">
                          {message.type === 'user' ? 'You' : (message.agent_name || 'VNASelf')}
                        </span>
                        <span className="message-time">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div 
                        className="message-text"
                        dangerouslySetInnerHTML={{ 
                          __html: formatMessage(message.content) 
                        }}
                      />
                    </div>
                  </div>
                ))}
                
                {isLoading && (
                  <div className="message assistant">
                    <div className="message-avatar">
                      <img src="/src/assets/qai_gen.png" alt="QAI" style={{ width: '150%', height: '150%', objectFit: 'contain', borderRadius: '50%' }} />
                    </div>
                    <div className="message-content">
                      <div className="message-header">
                        <span className="message-role">VNASelf</span>
                      </div>
                      <div className="message-text">
                        <div className="typing-indicator">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input */}
              <div className="chat-input-container">
                <div className="chat-input">
                  <div className="input-controls-left">
                    <button className="input-btn">+</button>
                  </div>
                  <input
                    ref={inputRef}
                    type="text"
                    placeholder="Type your message..."
                    value={inputValue}
                    onChange={handleInputChange}
                    onKeyPress={handleKeyPress}
                    className="chat-input-field"
                    disabled={isLoading}
                  />
                  <div className="input-controls-right">
                    <button 
                      className="send-btn" 
                      onClick={handleSendMessage}
                      disabled={!inputValue.trim() || isLoading}
                    >
                      →
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default App