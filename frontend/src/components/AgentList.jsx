import React from 'react'
import './AgentList.css'
import { Bitcoin } from 'lucide-react';
import { CalendarDays } from 'lucide-react';
import { Brain } from 'lucide-react';
import { FileText } from 'lucide-react';

const AgentList = ({ onAgentSelect }) => {
  // Available agents from the backend system
  const agents = [
    {
      id: 'supervisor',
      name: 'Supervisor Agent',
      description: 'Intelligent supervisor that routes requests to appropriate specialized agents',
      icon: <Brain size={24}/>,
      capabilities: ['Calendar Management', 'Finance Tracking', 'Smart Routing'],
      color: '#6366f1'
    },
    {
      id: 'calendar',
      name: 'Calendar Agent',
      description: 'Specialized agent for Google Calendar operations with conflict detection',
      icon: <CalendarDays size={24}/>,
      capabilities: ['Event Scheduling', 'Conflict Resolution', 'Time Optimization'],
      color: '#10b981'
    },
    {
      id: 'finance',
      name: 'Finance Agent',
      description: 'Smart financial assistant for expense tracking and budget management',
      icon: <Bitcoin size={24} />,
      capabilities: ['Expense Tracking', 'Budget Analysis', 'Spending Reports'],
      color: '#f59e0b'
    },
    {
      id: 'note',
      name: 'Note Agent',
      description: 'Record, classify, and retrieve your notes effortlessly',
      icon: <FileText size={24} />,
      capabilities: ['Note Taking', 'Auto Classification', 'Quick Retrieval'],
      color: '#3b82f6'
    }
  ]

  const handleAgentClick = (agent) => {
    onAgentSelect(agent)
  }

  return (
    <div className="agent-list-container">
      <div className="agent-list-header">
        <h2>Available Agents</h2>
        <p>Choose a specialized agent to help you with specific tasks</p>
      </div>
      
      <div className="agents-grid">
        {agents.map((agent) => (
          <div 
            key={agent.id}
            className="agent-card"
            onClick={() => handleAgentClick(agent)}
            style={{ '--agent-color': agent.color }}
          >
            <div className="agent-icon">{agent.icon}</div>
            <div className="agent-info">
              <h3 className="agent-name">{agent.name}</h3>
              <p className="agent-description">{agent.description}</p>
              <div className="agent-capabilities">
                {agent.capabilities.map((capability, index) => (
                  <span key={index} className="capability-tag">
                    {capability}
                  </span>
                ))}
              </div>
            </div>
            <div className="agent-arrow">→</div>
          </div>
        ))}
      </div>
      
      <div className="agent-list-footer">
        <p>Each agent is specialized for different types of tasks and will provide focused assistance.</p>
      </div>
    </div>
  )
}

export default AgentList
