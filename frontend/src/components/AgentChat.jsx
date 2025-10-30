import React, { useState, useEffect, useRef } from 'react'
import { useAuth } from '../contexts/AuthContext'
import FinanceChart from './FinanceChart'

const AgentChat = ({ agent, onBack }) => {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showWelcome, setShowWelcome] = useState(true)
  const [currentThreadId, setCurrentThreadId] = useState(null)
  const [currentLanguage, setCurrentLanguage] = useState(0)
  const [isTransitioning, setIsTransitioning] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const { user } = useAuth()

  // Agent-specific welcome messages and suggestions
  const agentWelcomeData = {
    supervisor: {
      title: 'Supervisor Agent',
      subtitle: 'Your intelligent assistant for routing tasks',
      suggestions: [
        'Schedule a team meeting for next week',
        'Add a new expense to my budget',
        'Check my calendar for conflicts',
        'Show me my spending summary'
      ]
    },
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
    }
  }

  const welcomeData = agentWelcomeData[agent.id] || agentWelcomeData.supervisor

  // AI Warning text in multiple languages
  const aiWarningTexts = [
    "AI-generated content may not always be accurate. Please verify important information independently.", // English
    "AIが生成したコンテンツは常に正確とは限りません。重要な情報は独立して確認してください。", // Japanese
    "Nội dung do AI tạo ra có thể không phải lúc nào cũng chính xác. Vui lòng xác minh lại thật kĩ.", // Vietnamese
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
    }, 6000) // Change every 6 seconds
    
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

  const sendMessage = async (content = inputValue) => {
    if (!content.trim()) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setShowWelcome(false)
    setInputValue('')

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: content.trim(),
          thread_id: currentThreadId,
          user_id: user?.id || 'default_user',
          agent_type: agent.id // Specify which agent to use
        })
      })

      if (response.ok) {
        const data = await response.json()
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: data.content || 'No response received',
          timestamp: new Date().toISOString()
        }

        setMessages(prev => [...prev, assistantMessage])
        
        if (data.thread_id) {
          setCurrentThreadId(data.thread_id)
        }
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || 'Failed to send message')
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion)
  }

  const formatMessage = (content) => {
    if (!content || typeof content !== 'string') return ''
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
            <div className="chat-input">
              <div className="input-controls-left">
                <button className="input-btn">+</button>
              </div>
              <input
                ref={inputRef}
                type="text"
                placeholder={`How can ${agent.name} help you today?`}
                value={inputValue}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                className="chat-input-field"
              />
              <div className="input-controls-right">
                <button 
                  className="send-btn" 
                  onClick={() => sendMessage()}
                  disabled={!inputValue.trim()}
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
                   <div
                     className="message-text"
                     dangerouslySetInnerHTML={{
                       __html: formatMessage(message.content || '')
                     }}
                   />
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
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
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
            <div className="chat-input">
              <div className="input-controls-left">
                <button className="input-btn">+</button>
              </div>
              <input
                ref={inputRef}
                type="text"
                placeholder={`Type your message to ${agent.name}...`}
                value={inputValue}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                className="chat-input-field"
                disabled={isLoading}
              />
               <div className="input-controls-right">
                 <button 
                   className="send-btn" 
                   onClick={() => sendMessage()}
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
  )
}

export default AgentChat