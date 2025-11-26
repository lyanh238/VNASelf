//main-content interface

import { useState, useEffect, useRef } from 'react'
import LampToggle from '../LampToggle'
import EyesTracking from '../EyesTracking'
import { useAuth } from '../contexts/AuthContext'
import AgentList from './AgentList'
import AgentChat from './AgentChat'
import ConversationList from './ConversationList'
import { MessageCirclePlus } from 'lucide-react';
import { MessageSquarePlus } from 'lucide-react';
import { Bot } from 'lucide-react';
import { FileText } from 'lucide-react';
import { ScanLine, Upload, X } from 'lucide-react';


const ChatApp = () => {
  const [inputValue, setInputValue] = useState('')
  const [selectedModel, setSelectedModel] = useState('gpt-4o')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [isDarkMode, setIsDarkMode] = useState(true)
  const [greeting, setGreeting] = useState('')
  const [isGreetingChanging, setIsGreetingChanging] = useState(false)
  const [currentThreadId, setCurrentThreadId] = useState(null)
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [showWelcome, setShowWelcome] = useState(true)
  const [currentLanguage, setCurrentLanguage] = useState(0)
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [currentView, setCurrentView] = useState('main') // 'main', 'agents', 'agent-chat'
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [conversations, setConversations] = useState([])
  const [currentConversation, setCurrentConversation] = useState(null)
  const [showSearchOptions, setShowSearchOptions] = useState(false)
  const [isWebSearchMode, setIsWebSearchMode] = useState(false)
  const [selectedTool, setSelectedTool] = useState(null)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const inputRef = useRef(null)
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)
  const { user, logout } = useAuth()

  // Close search options when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showSearchOptions && !event.target.closest('.input-controls-left')) {
        setShowSearchOptions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showSearchOptions])

  // Reset web search mode when switching views
  useEffect(() => {
    if (currentView !== 'main') {
      setIsWebSearchMode(false)
      setShowSearchOptions(false)
      setSelectedTool(null)
    }
  }, [currentView])

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

  // AI Warning text in multiple languages
  const aiWarningTexts = [
    "AI-generated content may not always be accurate. Please verify important information independently.", // English
    "AIが生成したコンテンツは常に正確とは限りません。重要な情報は独立して確認してください。", // Japanese
    "Nội dung do AI tạo ra có thể không phải lúc nào cũng chính xác. Vui lòng xác minh lại thật kĩ trước khi dùng.", // Vietnamese
    "AI生成的内容可能并不总是准确的。请独立验证重要信息。" // Chinese
  ]

  // Language rotation effect with smooth transition
  useEffect(() => {
    const interval = setInterval(() => {
      // Phase 1: Fade out slowly
      setIsTransitioning(true)
      
      // Phase 2: Change language after fade out completes
      setTimeout(() => {
        setCurrentLanguage((prev) => (prev + 1) % aiWarningTexts.length)
      }, 800) // Wait for fade out to complete
      
      // Phase 3: Fade in slowly
      setTimeout(() => {
        setIsTransitioning(false)
      }, 1000) // Start fade in after language change
    }, 20000) // Change every 6 seconds
    
    return () => clearInterval(interval)
  }, [])

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
        // Process messages to ensure proper user information
        const processedMessages = (data.messages || []).map(message => {
          if (message.message_type === 'user' || message.type === 'user') {
            return {
              ...message,
              type: 'user',
              user_name: message.metadata?.user_name || user?.name || 'You'
            }
          } else {
            return {
              ...message,
              type: 'assistant',
              agent_name: message.agent_name || 'X23D8'
            }
          }
        })
        setMessages(processedMessages)
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
          user_id: user?.id || user?.email || 'default_user',
          model_name: selectedModel,
          locale: (navigator?.language || navigator?.userLanguage || 'vi-VN')
        })
      })

      if (response.ok) {
        const data = await response.json()
        
        // Update thread ID if this is a new conversation
        if (!currentThreadId) {
          setCurrentThreadId(data.thread_id)
          // Refresh conversation list to show the new conversation
          if (user?.id) {
            // We'll let the ConversationList component handle this
          }
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
      if (selectedTool === 'web-search') {
        // Send web search query
        sendMessage(`Tìm kiếm web: ${inputValue}`)
        setSelectedTool(null)
        setIsWebSearchMode(false)
      } else if (selectedTool === 'document-search') {
        // Send document search query
        sendMessage(`Tìm kiếm tài liệu: ${inputValue}`)
        setSelectedTool(null)
        setIsWebSearchMode(false)
      } else {
        // Send normal message
        sendMessage(inputValue)
      }
      setInputValue('')
    }
  }

  const handleToolSelect = (tool) => {
    setSelectedTool(tool)
    setIsWebSearchMode(true)
    setShowSearchOptions(false)
    // Focus input field
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }

  const handleCancelSearch = () => {
    setIsWebSearchMode(false)
    setSelectedTool(null)
  }

  const getPlaceholderText = () => {
    if (selectedTool === 'web-search') {
      return "Nhập từ khóa tìm kiếm web..."
    } else if (selectedTool === 'document-search') {
      return "Nhập từ khóa tìm kiếm tài liệu..."
    } else if (selectedTool === 'ocr-process') {
      return "upload ảnh hoặc nhập đường dẫn"
    }
    return "How can I help you today?"
  }

  const getToolDisplayName = () => {
    if (selectedTool === 'web-search') {
      return "Web Search"
    } else if (selectedTool === 'document-search') {
      return "Document Search"
    } else if (selectedTool === 'ocr-process') {
      return "OCR Processing"
    }
    return "Search"
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
    setCurrentView('main')
    setSelectedAgent(null)
    setCurrentConversation(null)
    setUploadedFile(null)
    setSelectedTool(null)
    setIsWebSearchMode(false)
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setUploadedFile(file)
      setSelectedTool('ocr-process')
      setIsWebSearchMode(true)
    }
  }

  const handleFileUpload = async () => {
    if (!uploadedFile) return

    setIsUploading(true)
    setShowWelcome(false)

    // Show user message about file upload
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: `Đang xử lý file: ${uploadedFile.name}`,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])

    try {
      const formData = new FormData()
      formData.append('file', uploadedFile)
      formData.append('user_id', user?.id || user?.email || 'default_user')
      if (currentThreadId) {
        formData.append('thread_id', currentThreadId)
      }

      const response = await fetch('/api/upload-and-process', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        
        // Update thread ID if this is a new conversation
        if (data.thread_id && !currentThreadId) {
          setCurrentThreadId(data.thread_id)
        }

        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: data.result || 'File processed successfully',
          timestamp: new Date().toISOString()
        }

        setMessages(prev => [...prev, assistantMessage])
        setUploadedFile(null)
        setSelectedTool(null)
        setIsWebSearchMode(false)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || 'Failed to process file')
      }
    } catch (error) {
      console.error('Error uploading file:', error)
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: `Lỗi khi xử lý file: ${error.message}`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsUploading(false)
    }
  }

  const handleRemoveFile = () => {
    setUploadedFile(null)
    setSelectedTool(null)
    setIsWebSearchMode(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleConversationSelect = async (conversation) => {
    setCurrentConversation(conversation)
    setCurrentThreadId(conversation.thread_id)
    setShowWelcome(false)
    
    // Load the conversation history
    await loadChatHistory(conversation.thread_id)
  }

  const refreshConversations = () => {
    // This will be called by ConversationList when needed
    // We can add logic here if needed
  }

  // Agent routing functions
  const handleAgentClick = () => {
    setCurrentView('agents')
  }

  const handleAgentSelect = (agent) => {
    setSelectedAgent(agent)
    setCurrentView('agent-chat')
  }

  const handleBackToAgents = () => {
    setCurrentView('agents')
    setSelectedAgent(null)
  }

  const handleBackToMain = () => {
    setCurrentView('main')
    setSelectedAgent(null)
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
    if (!content || typeof content !== 'string') return ''
    // Check if content already contains HTML tags (from OCR agent or other sources)
    const hasHTML = /<[a-z][\s\S]*>/i.test(content)
    if (hasHTML) {
      // If content has HTML, return as-is (already formatted)
      return content
    }
    // Otherwise, apply markdown formatting
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
          <span>X2D35 — V.0.0.1</span>
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
          <div className="tiny-bar"></div>
          <div className="collapsed-rail">
            <button 
              className="rail-btn" 
              onClick={handleNewChat} 
              title="New chat" 
              aria-label="New chat"
            >
              <MessageSquarePlus size={20} strokeWidth={2} />
            </button>
            <button 
              className="rail-btn" 
              onClick={handleBackToMain}
              title="Chats" 
              aria-label="Chats"
            >
              <MessageCirclePlus size={20} strokeWidth={2} />
            </button>
            <button 
              className="rail-btn" 
              onClick={handleAgentClick}
              title="Agent" 
              aria-label="Agent"
            >
              <Bot size={20} strokeWidth={2} />
            </button>
          </div>
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

          <div className="sidebar-content">
            <nav className="navigation">
              <button 
                className={`nav-link`}
                onClick={handleNewChat}
              > 
                <span className="nav-icon">
                  <MessageSquarePlus size={20} strokeWidth={2} />
                </span>
                New chat
              </button>
            </nav>

            <nav className="navigation">
              <button 
                className={`nav-link ${currentView === 'main' ? 'active' : ''}`}
                onClick={handleBackToMain}
              > 
                <span className="nav-icon">
                  <MessageCirclePlus size={20} strokeWidth={2} />
                </span>
                Chats
              </button>
              <button 
                className={`nav-link ${currentView === 'agents' || currentView === 'agent-chat' ? 'active' : ''}`}
                onClick={handleAgentClick}
              >
                <span className="nav-icon">
                  <Bot size={20} strokeWidth={2} />
                </span>
                Agent
              </button>
            </nav>

            <div className="recents-section">
              <ConversationList 
                onConversationSelect={handleConversationSelect}
                currentThreadId={currentThreadId}
                onNewChat={handleNewChat}
                refreshTrigger={currentThreadId}
              />
            </div>
          </div>

          <div className="user-profile">
            <button className="user-profile-btn">
              <div className="user-avatar">{user?.name?.charAt(0) || 'U'}</div>
              <div className="user-info">
                <div className="user-name">{user?.name || 'User'}</div>
                {/* <div className="user-plan">Free plan</div> */}
              </div>
              <div className="user-dropdown" onClick={logout}>▼</div>
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="main-content">
          {currentView === 'main' && (
            <>
              {showWelcome && messages.length === 0 ? (
                <>
                  <div className="welcome-section">
                <div className="X2D35-icon-large">
                  <EyesTracking inputRef={inputRef} />
                </div>
                <h1 className={`welcome-text ${isGreetingChanging ? 'greeting-change' : ''}`}>
                  {greeting}, {user?.name || 'User'}
                </h1>
              </div>

              <div className="chat-input-container">
                <div className="chat-input">
                    <div className="input-controls-left">
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,.jpg,.jpeg,.png,.bmp,.tiff,.tif,.webp,.txt,.docx,.csv"
                        onChange={handleFileSelect}
                        style={{ display: 'none' }}
                      />
                      <button 
                        className="input-btn" 
                        onClick={() => fileInputRef.current?.click()}
                        title="Upload file for OCR"
                        disabled={isLoading || isUploading}
                      >
                        <Upload size={18} />
                      </button>
                      <button 
                        className="input-btn" 
                        onClick={() => setShowSearchOptions(!showSearchOptions)}
                        title="Tùy chọn tìm kiếm"
                        disabled={isLoading || isUploading}
                      >
                        +
                      </button>
                    <div className={`search-options ${showSearchOptions ? 'show' : ''}`}>
                      <div className="search-option" onClick={() => handleToolSelect('web-search')}>
                        <span>🌐</span>
                        <span>Web Search</span>
                      </div>
                          <div className="search-option" onClick={() => handleToolSelect('ocr-process')}>
                            <ScanLine size={15} strokeWidth={2} />
                            <span>OCR Processing</span>
                          </div>
                      <div className="search-option" onClick={() => handleToolSelect('document-search')}>
                        <FileText size={15} strokeWidth={2} />
                        <span>Document Search</span>
                      </div>
                    </div>
                  </div>
                  <input
                    ref={inputRef}
                    type="text"
                    placeholder={getPlaceholderText()}
                    value={inputValue}
                    onChange={handleInputChange}
                    onKeyPress={handleKeyPress}
                    className="chat-input-field"
                    disabled={isLoading || isUploading}
                  />
                  {isWebSearchMode && selectedTool && (
                    <div className="web-search-indicator-blue">
                      <span className="web-search-icon">
                        {selectedTool === 'web-search' ? '🌐' : 
                         selectedTool === "document-search" ? (
                            <FileText size={15} strokeWidth={2} />
                          ) : selectedTool === "ocr-process" ? (
                            <ScanLine size={15} strokeWidth={2} />
                          ) : (
                            <FileText size={15} strokeWidth={2} />
                          )
                        }
                      </span>
                      <span className="web-search-text">{getToolDisplayName()}</span>
                      <button 
                        className="cancel-web-search" 
                        onClick={handleCancelSearch}
                        title="Hủy tìm kiếm"
                      >
                        ✕
                      </button>
                    </div>
                  )}
                  <div className="input-controls-right">
                    <select 
                      value={selectedModel} 
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="model-select"
                    >
                      <option value="gpt-4o">GPT-4o</option>
                      <option value="gpt-4o-mini">GPT-4o Mini</option>
                      <option value="gpt-4.1">GPT-4.1</option>
                    </select>
                    <button 
                      className="send-btn" 
                      onClick={handleSendMessage}
                      disabled={!inputValue.trim() || isLoading || isUploading}
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
                  <span></span>
                  <span>Schedule Appointment</span>
                </button>
                <button 
                  className="prompt-btn"
                  onClick={() => handlePromptClick('Check available time slots')}
                >
                  <span></span>
                  <span>Check Schedule</span>
                </button>
                <button 
                  className="prompt-btn"
                  onClick={() => handlePromptClick('How to save money?')}
                >
                  <span></span>
                  <span>Finance Advice</span>
                </button>
                <button 
                  className="prompt-btn"
                  onClick={() => handlePromptClick('What is my payment status?')}
                >
                  <span></span>
                  <span>My payments</span>
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
                      {message.type === 'user' ? (
                        <div className="user-avatar">
                          {(message.user_name || user?.name) ? (message.user_name || user?.name).charAt(0).toUpperCase() : 'U'}
                        </div>
                      ) : (
                        <img src="/src/assets/qai_gen.png" alt="QAI" style={{ width: '150%', height: '150%', objectFit: 'contain', borderRadius: '50%' }} />
                      )}
                    </div>
                    <div className="message-content">
                      <div className="message-header">
                        <span className="message-role">
                          {message.type === 'user' ? (message.user_name || user?.name || 'You') : (message.agent_name || 'X23D8')}
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
                        <span className="message-role">X23D8</span>
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
                {uploadedFile && (
                  <div style={{
                    padding: '8px 12px',
                    marginBottom: '8px',
                    background: 'var(--bg-secondary)',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    border: '1px solid var(--border-color)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Upload size={16} />
                      <span style={{ fontSize: '14px', color: 'var(--text-primary)' }}>
                        {uploadedFile.name}
                      </span>
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                        ({(uploadedFile.size / 1024).toFixed(1)} KB)
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={handleFileUpload}
                        disabled={isUploading || isLoading}
                        style={{
                          padding: '4px 12px',
                          background: '#8b5cf6',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: (isUploading || isLoading) ? 'not-allowed' : 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        {isUploading ? 'Đang xử lý...' : 'Xử lý OCR'}
                      </button>
                      <button
                        onClick={handleRemoveFile}
                        style={{
                          padding: '4px 8px',
                          background: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          color: 'var(--text-muted)'
                        }}
                      >
                        <X size={16} />
                      </button>
                    </div>
                  </div>
                )}
                <div className="chat-input">
                  <div className="input-controls-left">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.bmp,.tiff,.tif,.webp,.txt,.docx,.csv"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
                    <button 
                      className="input-btn" 
                      onClick={() => fileInputRef.current?.click()}
                      title="Upload file for OCR"
                      disabled={isLoading || isUploading}
                    >
                      <Upload size={18} />
                    </button>
                    <button 
                      className="input-btn" 
                      onClick={() => setShowSearchOptions(!showSearchOptions)}
                      title="Tùy chọn tìm kiếm"
                      disabled={isLoading || isUploading}
                    >
                      +
                    </button>
                    <div className={`search-options ${showSearchOptions ? 'show' : ''}`}>
                      <div className="search-option" onClick={() => handleToolSelect('web-search')}>
                        <span>🌐</span>
                        <span>Web Search</span>
                      </div>
                      <div className="search-option" onClick={() => handleToolSelect('document-search')}>
                        <FileText size={15} strokeWidth={2} />
                        <span>Document Search</span>
                      </div>
                      <div className="search-option" onClick={() => handleToolSelect('ocr-process')}>
                        <ScanLine size={15} strokeWidth={2} />
                        <span>OCR Processing</span>
                      </div>
                    </div>
                  </div>
                  <input
                    ref={inputRef}
                    type="text"
                    placeholder={isWebSearchMode ? "Nhập từ khóa tìm kiếm web..." : "Type your message..."}
                    value={inputValue}
                    onChange={handleInputChange}
                    className="chat-input-field"
                    disabled={isLoading || isUploading}
                  />
                  {isWebSearchMode && selectedTool && (
                    <div className="web-search-indicator-blue">
                      <span className="web-search-icon">
                        {selectedTool === 'web-search' ? '🌐' : 
                         selectedTool === "document-search" ? (
                            <FileText size={15} strokeWidth={2} />
                          ) : selectedTool === "ocr-process" ? (
                            <ScanLine size={15} strokeWidth={2} />
                          ) : (
                            <FileText size={15} strokeWidth={2} />
                          )}
                      </span>
                      <span className="web-search-text">{getToolDisplayName()}</span>
                      <button 
                        className="cancel-web-search" 
                        onClick={handleCancelSearch}
                        title="Hủy tìm kiếm"
                      >
                        ✕
                      </button>
                    </div>
                  )}
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
                 
                 {/* AI Warning */}
                 <div style={{
                   fontSize: '12px',
                   color: 'var(--text-muted)',
                   marginTop: '8px',
                   padding: '8px 12px',
                   background: 'var(--bg-tertiary)',
                   borderRadius: '6px',
                   border: '1px solid var(--border-color)',
                   fontStyle: 'italic',
                   textAlign: 'center',
                   transition: 'all 1.2s ease-in-out',
                   opacity: isTransitioning ? 0 : 1,
                   transform: isTransitioning ? 'translateY(-15px) scale(0.9)' : 'translateY(0) scale(1)',
                   filter: isTransitioning ? 'blur(3px)' : 'blur(0)',
                   position: 'relative',
                   overflow: 'hidden'
                 }}>
                   <span style={{ 
                     position: 'relative', 
                     zIndex: 1,
                     display: 'block',
                     transition: 'opacity 1.2s ease-in-out'
                   }}>
                     {aiWarningTexts[currentLanguage]}
                   </span>
                 </div>
               </div>
              </>
            )}
            </>
          )}

          {currentView === 'agents' && (
            <AgentList onAgentSelect={handleAgentSelect} />
          )}

          {currentView === 'agent-chat' && selectedAgent && (
            <AgentChat 
              agent={selectedAgent} 
              onBack={handleBackToAgents}
            />
          )}
        </div>
      </div>
    </div>
  )
}

export default ChatApp
