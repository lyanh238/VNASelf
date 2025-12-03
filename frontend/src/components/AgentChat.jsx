import React, { useState, useEffect, useRef } from 'react'
import { useAuth } from '../contexts/AuthContext'
import FinanceChart from './FinanceChart'
import { Upload, X } from 'lucide-react'

const AgentChat = ({ agent, onBack }) => {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showWelcome, setShowWelcome] = useState(true)
  const [currentThreadId, setCurrentThreadId] = useState(null)
  const [currentLanguage, setCurrentLanguage] = useState(0)
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [ocrMethod, setOcrMethod] = useState('docling')
  const [ocrPrompt, setOcrPrompt] = useState('')
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const fileInputRef = useRef(null)
  const { user } = useAuth()

  // Agent-specific welcome messages and suggestions
  const agentWelcomeData = {
    calendar: {
      title: 'Calendar Agent',
      subtitle: 'Specialized in calendar management and scheduling',
      suggestions: [
        'Schedule a meeting for tomorrow at 2 PM',
        'Check my availability next week',
        'Suggest optimal time for focus work',
        'Show my upcoming events'
      ]
    },
    finance: {
      title: 'Finance Agent',
      subtitle: 'Your personal finance and expense tracking assistant',
      suggestions: [
        'Add a new expense: Coffee $5',
        'Show my spending this month',
        'What are my biggest expense categories?',
        'Show spending trend and forecast'
      ]
    },
    note: {
      title: 'Note Agent',
      subtitle: 'Capture and organize your notes with automatic categorization',
      suggestions: [
        'Note: Buy milk and eggs on Friday',
        'Remember to call mom this weekend',
        'Save this idea: build a habit tracker',
        'List my recent notes in Work category'
      ]
    },
    ocr: {
      title: 'OCR Agent',
      subtitle: 'Extract and search text from documents and images',
      suggestions: [
      ]
    }
  }

  const welcomeData = agentWelcomeData[agent.id] || agentWelcomeData.supervisor

  // AI Warning text in multiple languages
  const aiWarningTexts = [
    "AI-generated content may not always be accurate. Please verify important information independently.", // English
    "AIが生成したコンテンツは常に正確とは限りません。重要な情報は独立して確認してください。", // Japanese
    "Nội dung do AI tạo ra có thể không phải lúc nào cũng chính xác. Vui lòng xác minh lại trước khi dùng.", // Vietnamese
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
    }, 1000) // Change every 6 seconds
    
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }, [])

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setShowWelcome(true)
    setInputValue('')
    setCurrentThreadId(null)
  }

  const handleInputChange = (e) => {
    setInputValue(e.target.value)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const sendMessage = async (content = inputValue) => {
    // For OCR agent: if there's both file and prompt, auto-process OCR
    if (agent.id === 'ocr' && uploadedFile && content.trim()) {
      // Auto-trigger OCR processing with prompt
      await handleFileUploadWithPrompt(content.trim())
      return
    }

    if (!content.trim() && !uploadedFile) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: content.trim() || `Uploaded file: ${uploadedFile?.name || ''}`,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setShowWelcome(false)
    const promptToUse = content.trim()
    setInputValue('')

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: promptToUse,
          thread_id: currentThreadId,
          user_id: user?.id || 'default_user',
          agent_type: agent.id // Specify which agent to use
        })
      })

      if (response.ok) {
        const data = await response.json()
        
        // Remove processing message and add actual result
        setMessages(prev => {
          const filtered = prev.filter(msg => !msg.isProcessing)
          const assistantMessage = {
            id: Date.now() + 1,
            type: 'assistant',
            content: data.content || 'No response received',
            timestamp: new Date().toISOString()
          }
          return [...filtered, assistantMessage]
        })
        
        if (data.thread_id) {
          setCurrentThreadId(data.thread_id)
        }
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || 'Failed to send message')
      }
    } catch (error) {
      console.error('Error sending message:', error)
      // Remove processing message and add error
      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.isProcessing)
        const errorMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date().toISOString()
        }
        return [...filtered, errorMessage]
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion)
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setUploadedFile(file)
    }
  }

  const handleFileUploadWithPrompt = async (prompt = null) => {
    if (!uploadedFile) return

    setIsUploading(true)
    setIsLoading(true)
    setShowWelcome(false)

    // Get prompt from parameter, input field, or container
    const promptToUse = prompt || inputValue.trim() || ocrPrompt.trim()

    // Show user message about file upload
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: promptToUse || `Uploaded file: ${uploadedFile.name}`,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])
    
    // Show processing message immediately
    const processingMessage = {
      id: Date.now() + 1,
      type: 'assistant',
      content: 'Processing...',
      timestamp: new Date().toISOString(),
      isProcessing: true
    }
    setMessages(prev => [...prev, processingMessage])

    try {
      const formData = new FormData()
      formData.append('file', uploadedFile)
      formData.append('user_id', user?.id || user?.email || 'default_user')
      formData.append('ocr_method', ocrMethod)
      if (promptToUse) {
        formData.append('user_prompt', promptToUse)
      }
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

        // Remove processing message and add actual result
        setMessages(prev => {
          const filtered = prev.filter(msg => !msg.isProcessing)
          const assistantMessage = {
            id: Date.now() + 1,
            type: 'assistant',
            content: data.result || 'File processed successfully',
            timestamp: new Date().toISOString(),
            ocrHtmlUrl: data.html_url || null,
            ocrHtmlFilename: data.html_file || null
          }
          return [...filtered, assistantMessage]
        })
        setUploadedFile(null)
        setOcrPrompt('')
        setInputValue('') // Clear input after processing
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
        content: `Error processing file: ${error.message}`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsUploading(false)
      setIsLoading(false)
    }
  }

  const handleFileUpload = async () => {
    // Use the new function with prompt from input
    await handleFileUploadWithPrompt()
  }

  const handleRemoveFile = () => {
    setUploadedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
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
    <>
      {/* Back Button */}
      <div style={{ 
        position: 'absolute', 
        top: '72px', 
        left: '20px', 
        zIndex: 10 
      }}>
        <button 
          className="back-btn" 
          onClick={onBack}
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            padding: '8px 16px',
            color: 'var(--text-primary)',
            fontSize: '14px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.2s ease',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}
          onMouseEnter={(e) => {
            e.target.style.background = 'var(--bg-tertiary)'
            e.target.style.transform = 'translateY(-1px)'
            e.target.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)'
          }}
          onMouseLeave={(e) => {
            e.target.style.background = 'var(--bg-secondary)'
            e.target.style.transform = 'translateY(0)'
            e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)'
          }}
        >
          <span style={{ fontSize: '16px' }}>←</span>
          <span>Back to Agents</span>
        </button>
      </div>

      {showWelcome && messages.length === 0 ? (
        <>
          <div className="welcome-section" style={{ paddingTop: '72px' }}>
            <div className="X2D35-icon-large">
              <div style={{ fontSize: '48px', color: agent.color }}>
                {agent.icon}
              </div>
            </div>
            <h1 className="welcome-text">
              {welcomeData.title}
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: '16px', marginBottom: '32px' }}>
              {welcomeData.subtitle}
            </p>
          </div>

          <div className="chat-input-container">
            {uploadedFile && (
              <div style={{
                padding: '12px',
                marginBottom: '8px',
                background: 'var(--bg-secondary)',
                borderRadius: '8px',
                border: '1px solid var(--border-color)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Upload size={16} />
                    <span style={{ fontSize: '14px', color: 'var(--text-primary)' }}>
                      {uploadedFile.name}
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      ({(uploadedFile.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
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
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <label style={{ fontSize: '12px', color: 'var(--text-muted)', minWidth: '80px' }}>
                      Phương pháp:
                    </label>
                    <select
                      value={ocrMethod}
                      onChange={(e) => setOcrMethod(e.target.value)}
                      style={{
                        flex: 1,
                        padding: '6px 8px',
                        background: 'var(--bg-primary)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '4px',
                        color: 'var(--text-primary)',
                        fontSize: '12px'
                      }}
                      disabled={isUploading}
                    >
                      <option value="docling">Docling (PDF & Image)</option>
                      <option value="openai">OpenAI Vision (Image)</option>
                    </select>
                  </div>
                  {ocrMethod === 'openai' && (
                    <div style={{ 
                      padding: '8px', 
                      background: 'var(--bg-tertiary)', 
                      borderRadius: '4px',
                      fontSize: '11px',
                      color: 'var(--text-muted)',
                      fontStyle: 'italic'
                    }}>
                     Enter your prompt in the input field above and press Enter to process
                    </div>
                  )}
                  {!inputValue.trim() && (
                    <button
                      onClick={handleFileUpload}
                      disabled={isUploading || isLoading}
                      style={{
                        padding: '6px 12px',
                        background: agent.color,
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: (isUploading || isLoading) ? 'not-allowed' : 'pointer',
                        fontSize: '12px',
                        alignSelf: 'flex-end'
                      }}
                    >
                      {isUploading ? 'Processing...' : 'Process OCR'}
                    </button>
                  )}
                  {inputValue.trim() && (
                    <div style={{ 
                      padding: '8px', 
                      background: 'var(--bg-tertiary)', 
                      borderRadius: '4px',
                      fontSize: '11px',
                      color: 'var(--text-muted)',
                      fontStyle: 'italic',
                      alignSelf: 'flex-end'
                    }}>
                      Press Enter or click Send to process
                    </div>
                  )}
                </div>
              </div>
            )}
            <div className="chat-input">
              <div className="input-controls-left">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.bmp,.tiff,.tif"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
                <button 
                  className="input-btn"
                  onClick={() => fileInputRef.current?.click()}
                  title="Upload file for OCR"
                >
                  <Upload size={18} />
                </button>
              </div>
              <input
                ref={inputRef}
                type="text"
                placeholder={agent.id === 'ocr' 
                  ? (uploadedFile ? "Enter your prompt and press Enter to process..." : "Upload an image and enter your prompt...")
                  : `How can ${agent.name} help you today?`}
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                className="chat-input-field"
                disabled={isUploading || isLoading}
              />
              <div className="input-controls-right">
                <button 
                  className="send-btn" 
                  onClick={() => sendMessage()}
                  disabled={!inputValue.trim() || isUploading}
                >
                  →
                </button>
              </div>
            </div>
          </div>

          <div className="prompt-suggestions">
            {welcomeData.suggestions.map((suggestion, index) => (
              <button 
                key={index}
                className="prompt-btn"
                onClick={() => handleSuggestionClick(suggestion)}
              >
                <span></span>
                <span>{suggestion}</span>
              </button>
            ))}
          </div>
        </>
      ) : (
        <>
          {/* Chat Messages */}
          <div className="chat-messages" style={{ paddingTop: '72px' }}>
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.type}`}>
                <div className="message-avatar">
                  {message.type === 'user' ? 'U' : (
                    <div style={{ 
                      width: '32px', 
                      height: '32px', 
                      borderRadius: '50%', 
                      background: agent.color,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '16px',
                      color: 'white'
                    }}>
                      {agent.icon}
                    </div>
                  )}
                </div>
                <div className="message-content">
                  <div className="message-header">
                    <span className="message-role">
                      {message.type === 'user' ? 'You' : agent.name}
                    </span>
                    <span className="message-time">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  {message.isProcessing ? (
                    <div className="message-text">
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '8px',
                        color: 'var(--text-muted)',
                        fontStyle: 'italic'
                      }}>
                        <span>Processing</span>
                        <div className="typing-indicator" style={{ margin: 0 }}>
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div
                        className="message-text"
                        dangerouslySetInnerHTML={{
                          __html: formatMessage(message.content || '')
                        }}
                      />
                      {message.ocrHtmlUrl && (
                        <div className="ocr-attachment">
                          <div className="ocr-download-container">
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
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="message assistant">
                <div className="message-avatar">
                  <div style={{ 
                    width: '32px', 
                    height: '32px', 
                    borderRadius: '50%', 
                    background: agent.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '16px',
                    color: 'white'
                  }}>
                    {agent.icon}
                  </div>
                </div>
                <div className="message-content">
                  <div className="message-header">
                    <span className="message-role">{agent.name}</span>
                  </div>
                  <div className="message-text">
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px',
                      color: 'var(--text-muted)',
                      fontStyle: 'italic'
                    }}>
                      <span>Processing</span>
                      <div className="typing-indicator" style={{ margin: 0 }}>
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
            {/* Finance interactive charts */}
            {agent.id === 'finance' && (
              <div style={{ marginTop: '12px' }}>
                <FinanceChart userId={user?.id || 'default_user'} />
              </div>
            )}
          </div>

          {/* Chat Input */}
          <div className="chat-input-container">
            {uploadedFile && (
              <div style={{
                padding: '12px',
                marginBottom: '8px',
                background: 'var(--bg-secondary)',
                borderRadius: '8px',
                border: '1px solid var(--border-color)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Upload size={16} />
                    <span style={{ fontSize: '14px', color: 'var(--text-primary)' }}>
                      {uploadedFile.name}
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      ({(uploadedFile.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
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
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <label style={{ fontSize: '12px', color: 'var(--text-muted)', minWidth: '80px' }}>
                      Phương pháp:
                    </label>
                    <select
                      value={ocrMethod}
                      onChange={(e) => setOcrMethod(e.target.value)}
                      style={{
                        flex: 1,
                        padding: '6px 8px',
                        background: 'var(--bg-primary)',
                        border: '1px solid var(--border-color)',
                        borderRadius: '4px',
                        color: 'var(--text-primary)',
                        fontSize: '12px'
                      }}
                      disabled={isUploading || isLoading}
                    >
                      <option value="docling">Docling (PDF & Ảnh)</option>
                      <option value="openai">OpenAI Vision (Chỉ ảnh)</option>
                    </select>
                  </div>
                  {ocrMethod === 'openai' && (
                    <div style={{ 
                      padding: '8px', 
                      background: 'var(--bg-tertiary)', 
                      borderRadius: '4px',
                      fontSize: '11px',
                      color: 'var(--text-muted)',
                      fontStyle: 'italic'
                    }}>
                      💡 Enter your prompt in the input field above and press Enter to process
                    </div>
                  )}
                  {!inputValue.trim() && (
                    <button
                      onClick={handleFileUpload}
                      disabled={isUploading || isLoading}
                      style={{
                        padding: '6px 12px',
                        background: agent.color,
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: (isUploading || isLoading) ? 'not-allowed' : 'pointer',
                        fontSize: '12px',
                        alignSelf: 'flex-end'
                      }}
                    >
                      {isUploading ? 'Processing...' : 'Process OCR'}
                    </button>
                  )}
                  {inputValue.trim() && (
                    <div style={{ 
                      padding: '8px', 
                      background: 'var(--bg-tertiary)', 
                      borderRadius: '4px',
                      fontSize: '11px',
                      color: 'var(--text-muted)',
                      fontStyle: 'italic',
                      alignSelf: 'flex-end'
                    }}>
                      Press Enter or click Send to process
                    </div>
                  )}
                </div>
              </div>
            )}
            <div className="chat-input">
              <div className="input-controls-left">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.bmp,.tiff,.tif"
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
              </div>
              <input
                ref={inputRef}
                type="text"
                placeholder={agent.id === 'ocr' 
                  ? (uploadedFile ? "Enter your prompt and press Enter to process..." : "Upload an image and enter your prompt...")
                  : `Type your message to ${agent.name}...`}
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                className="chat-input-field"
                disabled={isLoading || isUploading}
              />
               <div className="input-controls-right">
                 <button 
                   className="send-btn" 
                   onClick={() => sendMessage()}
                   disabled={(!inputValue.trim() && !uploadedFile) || isLoading || isUploading}
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
  )
}

export default AgentChat