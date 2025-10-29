import React, { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { MessageCircle, Edit2, Trash2, RotateCcw, MoreHorizontal } from 'lucide-react'
import './ConversationList.css'

const ConversationList = ({ onConversationSelect, currentThreadId, onNewChat, refreshTrigger }) => {
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState(null)
  const [editTitle, setEditTitle] = useState('')
  const [showMenuId, setShowMenuId] = useState(null)
  const { user } = useAuth()

  useEffect(() => {
    if (user?.id || user?.email) {
      loadConversations()
    }
  }, [user?.id, user?.email, refreshTrigger])

  const loadConversations = async () => {
    try {
      setLoading(true)
      const userId = user?.id || user?.email || 'default_user'
      console.log('Loading conversations for user:', userId, 'User object:', user)
      const response = await fetch(`/api/conversations/${userId}`)
      if (response.ok) {
        const data = await response.json()
        console.log('Loaded conversations:', data)
        setConversations(data)
      } else {
        console.error('Failed to load conversations:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('Error loading conversations:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleConversationClick = (conversation) => {
    onConversationSelect(conversation)
  }

  const handleRename = async (conversationId, newTitle) => {
    try {
      const userId = user?.id || user?.email || 'default_user'
      const response = await fetch(`/api/conversations/${userId}/${conversationId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: newTitle }),
      })

      if (response.ok) {
        setConversations(prev => 
          prev.map(conv => 
            conv.thread_id === conversationId 
              ? { ...conv, title: newTitle }
              : conv
          )
        )
        setEditingId(null)
        setEditTitle('')
      } else {
        console.error('Failed to rename conversation')
      }
    } catch (error) {
      console.error('Error renaming conversation:', error)
    }
  }

  const handleDelete = async (conversationId) => {
    if (!window.confirm('Are you sure you want to delete this conversation? This action cannot be undone.')) {
      return
    }

    try {
      const userId = user?.id || user?.email || 'default_user'
      const response = await fetch(`/api/conversations/${userId}/${conversationId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        setConversations(prev => prev.filter(conv => conv.thread_id !== conversationId))
        // If we're currently viewing this conversation, go to new chat
        if (currentThreadId === conversationId) {
          onNewChat()
        }
      } else {
        console.error('Failed to delete conversation')
      }
    } catch (error) {
      console.error('Error deleting conversation:', error)
    }
  }

  const handleRegenerateTitle = async (conversationId) => {
    try {
      const userId = user?.id || user?.email || 'default_user'
      const response = await fetch(`/api/conversations/${userId}/${conversationId}/regenerate-title`, {
        method: 'POST',
      })

      if (response.ok) {
        const data = await response.json()
        setConversations(prev => 
          prev.map(conv => 
            conv.thread_id === conversationId 
              ? { ...conv, title: data.title }
              : conv
          )
        )
      } else {
        console.error('Failed to regenerate title')
      }
    } catch (error) {
      console.error('Error regenerating title:', error)
    }
  }

  const startEditing = (conversation) => {
    setEditingId(conversation.thread_id)
    setEditTitle(conversation.title)
  }

  const cancelEditing = () => {
    setEditingId(null)
    setEditTitle('')
  }

  const saveEdit = () => {
    if (editTitle.trim()) {
      handleRename(editingId, editTitle.trim())
    } else {
      cancelEditing()
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      saveEdit()
    } else if (e.key === 'Escape') {
      cancelEditing()
    }
  }

  const formatDate = (timestamp) => {
    if (!timestamp) return ''
    const date = new Date(timestamp)
    const now = new Date()
    const diffTime = Math.abs(now - date)
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 1) return 'Today'
    if (diffDays === 2) return 'Yesterday'
    if (diffDays <= 7) return `${diffDays - 1} days ago`
    return date.toLocaleDateString()
  }

  const groupConversationsByDate = (conversations) => {
    const groups = {
      'Today': [],
      'Yesterday': [],
      'This Week': [],
      'Older': []
    }

    conversations.forEach(conv => {
      const date = formatDate(conv.last_message_timestamp)
      if (date === 'Today') {
        groups['Today'].push(conv)
      } else if (date === 'Yesterday') {
        groups['Yesterday'].push(conv)
      } else if (date.includes('days ago') && parseInt(date) <= 7) {
        groups['This Week'].push(conv)
      } else {
        groups['Older'].push(conv)
      }
    })

    return groups
  }

  if (loading) {
    return (
      <div className="conversation-list">
        <div className="conversation-loading">
          <div className="loading-spinner"></div>
          <span>Loading conversations...</span>
        </div>
      </div>
    )
  }

  const groupedConversations = groupConversationsByDate(conversations)

  return (
    <div className="conversation-list">
      {conversations.length === 0 ? (
        <div className="no-conversations">
          <MessageCircle size={48} />
          <p>No conversations yet</p>
          <p>Start a new chat to begin!</p>
        </div>
      ) : (
        <div className="conversation-groups">
          {Object.entries(groupedConversations).map(([groupName, groupConversations]) => {
            if (groupConversations.length === 0) return null
            
            return (
              <div key={groupName} className="conversation-group">
                <h4 className="group-title">{groupName}</h4>
                {groupConversations.map((conversation) => (
                  <div
                    key={conversation.thread_id}
                    className={`conversation-item ${currentThreadId === conversation.thread_id ? 'active' : ''}`}
                    onClick={() => handleConversationClick(conversation)}
                  >
                    <div className="conversation-content">
                      {editingId === conversation.thread_id ? (
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyPress={handleKeyPress}
                          onBlur={saveEdit}
                          className="conversation-edit-input"
                          autoFocus
                        />
                      ) : (
                        <>
                          <div className="conversation-title">{conversation.title}</div>
                        </>
                      )}
                    </div>
                    
                    <div className="conversation-actions">
                      <button
                        className="conversation-menu-btn"
                        onClick={(e) => {
                          e.stopPropagation()
                          setShowMenuId(showMenuId === conversation.thread_id ? null : conversation.thread_id)
                        }}
                      >
                        <MoreHorizontal size={16} />
                      </button>
                      
                      {showMenuId === conversation.thread_id && (
                        <div className="conversation-menu">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              startEditing(conversation)
                              setShowMenuId(null)
                            }}
                          >
                            <Edit2 size={14} />
                            Rename
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleRegenerateTitle(conversation.thread_id)
                              setShowMenuId(null)
                            }}
                          >
                            <RotateCcw size={14} />
                            Regenerate Title
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDelete(conversation.thread_id)
                              setShowMenuId(null)
                            }}
                            className="delete-btn"
                          >
                            <Trash2 size={14} />
                            Delete
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default ConversationList
