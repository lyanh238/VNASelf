import { useState, useEffect, useRef } from 'react'
import { Upload } from 'lucide-react'
import './ChatInterface.css'
import FinanceChart from './components/FinanceChart'

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
  const [isUploading, setIsUploading] = useState(false)
  const [uploadingFileName, setUploadingFileName] = useState(null)
  const [thinkingStatus, setThinkingStatus] = useState(null) // 'thinking', 'planning', 'executing'
  const [isDragging, setIsDragging] = useState(false)
  const [droppedImage, setDroppedImage] = useState(null)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const fileInputRef = useRef(null)
  const thinkingTimersRef = useRef([])
  const dropZoneRef = useRef(null)

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
    
    // Clear any existing timers
    thinkingTimersRef.current.forEach(timer => clearTimeout(timer))
    thinkingTimersRef.current = []
    
    // Show thinking status progression with smooth transitions
    setThinkingStatus('thinking')
    const thinkingTimer = setTimeout(() => setThinkingStatus('planning'), 1000)
    const planningTimer = setTimeout(() => setThinkingStatus('executing'), 2000)
    
    // Store timers to clear if needed
    thinkingTimersRef.current = [thinkingTimer, planningTimer]

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
      setThinkingStatus(null)
      // Clear any pending timers
      thinkingTimersRef.current.forEach(timer => clearTimeout(timer))
      thinkingTimersRef.current = []
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

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      processFile(file)
      e.target.value = ''
    }
  }
  
  const processFile = (file) => {
    // Check if it's an image
    const imageTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff', 'image/tif', 'image/webp']
    if (imageTypes.includes(file.type)) {
      setDroppedImage(file)
      // Auto-upload images
      uploadDocument(file)
    } else {
      // For other files, use normal upload
      uploadDocument(file)
    }
  }
  
  // Drag and drop handlers
  const handleDragEnter = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }
  
  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }
  
  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }
  
  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    
    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      const file = files[0]
      processFile(file)
    }
  }

  const uploadDocument = async (file) => {
    setIsUploading(true)
    setUploadingFileName(file.name)

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: `Đã tải lên file: ${file.name}`,
      timestamp: new Date().toISOString()
    }

    const processingMessage = {
      id: Date.now() + 1,
      type: 'assistant',
      content: 'Đang xử lý...',
      timestamp: new Date().toISOString(),
      isProcessing: true
    }

    setMessages(prev => [...prev, userMessage, processingMessage])

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('user_id', 'default_user')
      if (currentThreadId) {
        formData.append('thread_id', currentThreadId)
      }

      const response = await fetch('/api/upload-and-process', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || 'Failed to process file')
      }

      const data = await response.json()

      if (data.thread_id && !currentThreadId) {
        setCurrentThreadId(data.thread_id)
        onThreadChange(data.thread_id)
      }

      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.isProcessing)
        const assistantMessage = {
          id: Date.now() + 2,
          type: 'assistant',
          content: data.result || 'File processed successfully',
          agent_name: 'OCR Agent',
          timestamp: new Date().toISOString(),
          ocrHtmlUrl: data.html_url || null,
          ocrHtmlFilename: data.html_file || null
        }
        const updated = [...filtered, assistantMessage]
        onChatHistoryChange(updated)
        return updated
      })
    } catch (error) {
      console.error('Error uploading document:', error)
      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.isProcessing)
        const errorMessage = {
          id: Date.now() + 3,
          type: 'assistant',
          content: `Lỗi khi xử lý file: ${error.message}`,
          agent_name: 'Error',
          timestamp: new Date().toISOString()
        }
        return [...filtered, errorMessage]
      })
    } finally {
      setIsUploading(false)
      setUploadingFileName(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
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

  const shouldShowChart = (content) => {
    const chartKeywords = [
      'biểu đồ', 'chart', 'vẽ biểu đồ', 'hiển thị biểu đồ',
      'dự báo', 'forecast', 'prophet', 'xu hướng chi tiêu',
      'chi tiêu theo thời gian', 'spending trend'
    ]
    return chartKeywords.some(keyword => 
      content.toLowerCase().includes(keyword.toLowerCase())
    )
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
                <img src="frontend/public/qai_gen.png" alt="QAI" style={{ width: '150%', height: '150%', objectFit: 'contain', borderRadius: '50%' }} />
              )}
            </div>
            <div className="message-content">
              <div className="message-header">
            <span className="message-role">
              {message.type === 'user' ? 'Bạn' : (message.agent_name || 'X23D8')}
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
              {message.ocrHtmlUrl && (
                <div className="ocr-attachment" style={{ marginTop: '12px' }}>
                  <a
                    className="ocr-download-btn"
                    href={message.ocrHtmlUrl}
                    download={message.ocrHtmlFilename || 'ocr_result.html'}
                    rel="noopener noreferrer"
                  >
                    <span className="download-btn-icon">⬇️</span>
                    <span className="download-btn-text">Tải file HTML</span>
                  </a>
                  <div className="ocr-download-info">
                    <small>File HTML chứa toàn bộ nội dung Docling. Bạn có thể mở trực tiếp trong trình duyệt.</small>
                  </div>
                </div>
              )}
              {message.agent_name === 'Finance Agent' && shouldShowChart(message.content) && (
                <div style={{ marginTop: '16px' }}>
                  <FinanceChart userId="X2D35" />
                </div>
              )}
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
                {thinkingStatus === 'thinking' && (
                  <div className="status-indicator thinking">
                    <div className="status-icon">💭</div>
                    <span className="status-text">Đang suy nghĩ...</span>
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                )}
                {thinkingStatus === 'planning' && (
                  <div className="status-indicator planning">
                    <div className="status-icon">📋</div>
                    <span className="status-text">Đang lập kế hoạch...</span>
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                )}
                {thinkingStatus === 'executing' && (
                  <div className="status-indicator executing">
                    <div className="status-icon">⚙️</div>
                    <span className="status-text">Đang thực thi...</span>
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                )}
                {!thinkingStatus && (
                  <div className="status-indicator">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div 
        className="chat-input-container"
        ref={dropZoneRef}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={{
          position: 'relative',
          border: isDragging ? '2px dashed #8b5cf6' : 'none',
          borderRadius: isDragging ? '8px' : '0',
          background: isDragging ? 'rgba(139, 92, 246, 0.05)' : 'transparent'
        }}
      >
        {isDragging && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 1000,
            background: 'var(--bg-secondary)',
            padding: '20px 40px',
            borderRadius: '12px',
            border: '2px dashed #8b5cf6',
            pointerEvents: 'none'
          }}>
            <div style={{ textAlign: 'center', color: '#8b5cf6', fontWeight: '600' }}>
              Drop file here to upload
            </div>
          </div>
        )}
        {droppedImage && (
          <div style={{
            marginBottom: '8px',
            padding: '8px 12px',
            background: 'var(--bg-secondary)',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <img 
              src={URL.createObjectURL(droppedImage)} 
              alt="Preview" 
              style={{ width: '40px', height: '40px', objectFit: 'cover', borderRadius: '4px' }}
            />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '14px', color: 'var(--text-primary)' }}>{droppedImage.name}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                {(droppedImage.size / 1024).toFixed(1)} KB
              </div>
            </div>
            <button
              onClick={() => setDroppedImage(null)}
              style={{
                padding: '4px 8px',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--text-muted)'
              }}
            >
              ✕
            </button>
          </div>
        )}
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
            disabled={isLoading || isUploading}
          />
          <div className="input-controls-right">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.bmp,.tiff,.tif,.webp,.txt,.docx,.csv"
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
            <button
              className="input-btn upload-btn"
              onClick={() => fileInputRef.current?.click()}
              title="Upload file for OCR"
              disabled={isLoading || isUploading}
            >
              <Upload size={18} />
              <span className="upload-label">{isUploading ? 'Đang xử lý...' : 'OCR'}</span>
            </button>
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
      {uploadingFileName && (
        <div className="upload-status-banner">
          <span>Đang tải lên: {uploadingFileName}</span>
        </div>
      )}
    </div>
  )
}

export default ChatInterface
