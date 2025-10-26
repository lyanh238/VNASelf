import { useState, useEffect, useRef } from 'react'
import './ChatInterface.css'

const ChatInterface = ({ 
  threadId, 
  onThreadChange, 
  onChatHistoryChange, 
  onBackToHome,
  initialMessage = null
}) => {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState(initialMessage || '')
  const [isLoading, setIsLoading] = useState(false)
  const [currentThreadId, setCurrentThreadId] = useState(threadId)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

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

  useEffect(() => {
    // Scroll to bottom when component mounts
    scrollToBottom()
    // Focus the input field
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }, [])

  useEffect(() => {
    if (currentThreadId) {
      loadChatHistory(currentThreadId)
    }
  }, [currentThreadId])

  // Auto-send initial message if provided
  useEffect(() => {
    if (initialMessage && initialMessage.trim() && messages.length === 0) {
      sendMessage(initialMessage)
      setInputValue('')
    }
  }, [initialMessage, messages.length])

  const loadChatHistory = async (threadId) => {
    try {
      const response = await fetch(`/api/chat/history/${threadId}`)
      if (response.ok) {
        const data = await response.json()
        setMessages(data.messages || [])
        onChatHistoryChange(data.messages || [])
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
          onThreadChange(data.thread_id)
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
        
        // Update chat history
        const updatedHistory = [...messages, userMessage, assistantMessage]
        onChatHistoryChange(updatedHistory)
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

  const handleSendMessage = () => {
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
    <div className="chat-interface">
      <div className="chat-header">
        <button className="back-btn" onClick={onBackToHome}>
          ← Quay lại
        </button>
        <div className="chat-title">
          {currentThreadId ? `Cuộc trò chuyện ${currentThreadId.slice(0, 8)}` : 'Cuộc trò chuyện mới'}
        </div>
        <div className="chat-actions">
          <button className="action-btn">⋯</button>
        </div>
      </div>

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
              {message.type === 'user' ? 'Bạn' : (message.agent_name || 'VNASelf')}
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

      <div className="chat-input-container">
        <div className="chat-input">
          <div className="input-controls-left">
            <button className="input-btn">+</button>
          </div>
          <input
            ref={inputRef}
            type="text"
            placeholder="Nhập tin nhắn của bạn..."
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
    </div>
  )
}

export default ChatInterface
