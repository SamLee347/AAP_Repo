"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { MessageSquare, AlertCircle, CheckCircle } from 'lucide-react'

interface ChatMessage {
  type: "user" | "ai"
  content: string
  timestamp?: string
  rawContent?: string // Store original for debugging
}

interface ChatStatus {
  chatbot_available: boolean
  capabilities?: string[]
  status?: string
}

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000"

// Format chatbot response with proper HTML styling
function formatChatbotResponse(rawText: string): string {
  if (!rawText) return ""

  // Clean up numbers (remove excessive decimals)
  let formatted = rawText.replace(/(\d+\.\d{5,})/g, (num) => {
    return parseFloat(num).toFixed(2)
  })

  // Convert to HTML with proper formatting
  formatted = formatted
    // Headers
    .replace(/🔮 (.+?)(\n|$)/g, '<h3 class="response-header forecast-header">$1</h3>')
    .replace(/🔄 (.+?):/g, '<h4 class="response-subheader mapping-header">$1:</h4>')
    .replace(/🏆 (.+?)(\n|$)/g, '<h3 class="response-header performance-header">$1</h3>')
    .replace(/🗄️ (.+?)(\n|$)/g, '<h3 class="response-header database-header">$1</h3>')
    
    // Sections
    .replace(/\*\*(.+?):\*\*/g, '<strong class="section-title">$1:</strong>')
    
    // Lists with bullets
    .replace(/• (.+?): (.+?)(\n|$)/g, '<li class="response-item"><span class="item-label">$1:</span> <span class="item-value">$2</span></li>')
    .replace(/(\d+\.) (.+?)(\n|$)/g, '<li class="response-item numbered"><span class="number">$1</span> $2</li>')
    
    // Bold text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    
    // Line breaks
    .replace(/\n/g, '<br/>')
    
    // Clean up any double breaks
    .replace(/(<br\/>){3,}/g, '<br/><br/>')

  return formatted
}

export function ChatView() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [chatStatus, setChatStatus] = useState<ChatStatus | null>(null)
  const [connectionError, setConnectionError] = useState(false)

  // Check chatbot status on component mount
  useEffect(() => {
    checkChatbotStatus()
  }, [])

  const checkChatbotStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/status`)
      if (response.ok) {
        const status = await response.json()
        setChatStatus(status)
        setConnectionError(false)
      } else {
        setConnectionError(true)
      }
    } catch (error) {
      console.log("Could not connect to chatbot service")
      setConnectionError(true)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage: ChatMessage = { 
      type: "user", 
      content: input.trim(),
      timestamp: new Date().toISOString()
    }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input.trim() }),
      })

      const data = await response.json()
      
      if (response.ok && data.success) {
        const formattedContent = formatChatbotResponse(data.response)
        const aiMessage: ChatMessage = { 
          type: "ai", 
          content: formattedContent,
          rawContent: data.response, // Store original for debugging
          timestamp: data.timestamp || new Date().toISOString()
        }
        setMessages((prev) => [...prev, aiMessage])
        setConnectionError(false)
      } else {
        // Handle API errors (400, 503, etc.)
        const errorMessage: ChatMessage = {
          type: "ai",
          content: data.response || "Sorry, I encountered an error processing your request.",
        }
        setMessages((prev) => [...prev, errorMessage])
      }
    } catch (error) {
      console.error("Chat error:", error)
      setConnectionError(true)
      const errorMessage: ChatMessage = {
        type: "ai",
        content: "I'm having trouble connecting to the server. Please check if the Flask backend is running on http://localhost:5000",
      }
      setMessages((prev) => [...prev, errorMessage])
    }

    setInput("")
    setLoading(false)
  }

  const testConnection = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/chat/test`)
      if (response.ok) {
        const testData = await response.json()
        const formattedContent = formatChatbotResponse(testData.response)
        const testMessage: ChatMessage = {
          type: "ai",
          content: `<h3 class="response-header test-header">✅ Connection Test Successful!</h3>
                    <p><strong>Test Query:</strong> "${testData.test_message}"</p>
                    ${formattedContent}`,
          rawContent: testData.response
        }
        setMessages((prev) => [...prev, testMessage])
        setConnectionError(false)
      }
    } catch (error) {
      setConnectionError(true)
    }
    setLoading(false)
  }

  return (
    <div>
      <h2 className="mb-6 font-size-24 font-weight-600">
        AI Assistant
      </h2>
      
      {/* Status Bar */}
      <div className="mb-4 p-3" style={{ 
        backgroundColor: connectionError ? "#f8d7da" : "#d4edda", 
        border: `1px solid ${connectionError ? "#f5c6cb" : "#c3e6cb"}`,
        borderRadius: "4px",
        display: "flex",
        alignItems: "center",
        gap: "8px"
      }}>
        {connectionError ? (
          <>
            <AlertCircle size={16} color="#721c24" />
            <span style={{ color: "#721c24" }}>
              Backend disconnected. <button onClick={checkChatbotStatus} style={{ textDecoration: "underline", background: "none", border: "none", color: "#721c24", cursor: "pointer" }}>Retry connection</button>
            </span>
          </>
        ) : (
          <>
            <CheckCircle size={16} color="#155724" />
            <span style={{ color: "#155724" }}>
              Connected to AI Assistant
              {chatStatus?.capabilities && ` • Capabilities: ${chatStatus.capabilities.join(", ")}`}
            </span>
          </>
        )}
      </div>

      <div className="card">
        <div className="chat-container">
          {messages.length === 0 ? (
            <div className="chat-empty">
              <MessageSquare size={48} color="#ced4da" className="chat-empty-icon" />
              <p>Ask me anything about your inventory, orders, or operations!</p>
              {chatStatus?.capabilities && (
                <div style={{ marginTop: "12px", fontSize: "14px", color: "#6c757d" }}>
                  <strong>I can help with:</strong>
                  <ul style={{ listStyle: "none", padding: 0, margin: "8px 0 0 0" }}>
                    {chatStatus.capabilities.map((capability, idx) => (
                      <li key={idx}>• {capability}</li>
                    ))}
                  </ul>
                </div>
              )}
              {connectionError && (
                <button 
                  onClick={testConnection} 
                  disabled={loading}
                  className="btn btn-secondary"
                  style={{ marginTop: "12px" }}
                >
                  Test Connection
                </button>
              )}
            </div>
          ) : (
            <div className="chat-messages">
              {messages.map((msg, idx) => (
                <div key={idx} className={`message message-${msg.type}`}>
                  {msg.type === "ai" ? (
                    <div 
                      className="ai-response-content"
                      dangerouslySetInnerHTML={{ __html: msg.content }}
                    />
                  ) : (
                    msg.content
                  )}
                  {msg.timestamp && (
                    <div style={{ fontSize: "11px", opacity: 0.6, marginTop: "4px" }}>
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="message message-ai" style={{ opacity: 0.7 }}>
                  <div className="thinking-animation">
                    <span>●</span><span>●</span><span>●</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        <form onSubmit={handleSubmit} className="chat-input-container">
          <input
            type="text"
            placeholder="Ask about inventory, orders, analytics..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            className="chat-input form-input"
          />
          <button type="submit" disabled={loading || !input.trim()} className="btn btn-primary">
            {loading ? "..." : "Send"}
          </button>
        </form>
      </div>

      {/* Add some CSS for the formatted responses */}
      <style>{`
        .ai-response-content {
          line-height: 1.6;
        }
        
        .response-header {
          color: #2c5282;
          margin: 0 0 12px 0;
          font-weight: 600;
          font-size: 1.1em;
        }
        
        .response-subheader {
          color: #4a5568;
          margin: 12px 0 8px 0;
          font-weight: 500;
          font-size: 1em;
        }
        
        .response-item {
          margin: 6px 0;
          padding-left: 8px;
          border-left: 3px solid #e2e8f0;
        }
        
        .item-label {
          font-weight: 500;
          color: #4a5568;
        }
        
        .item-value {
          color: #2d3748;
        }
        
        .numbered {
          list-style-type: decimal;
          margin-left: 20px;
        }
        
        .section-title {
          color: #2c5282;
          display: block;
          margin: 12px 0 4px 0;
        }
        
        .thinking-animation span {
          animation: bounce 1.5s infinite;
          display: inline-block;
          margin: 0 2px;
        }
        
        .thinking-animation span:nth-child(2) {
          animation-delay: 0.2s;
        }
        
        .thinking-animation span:nth-child(3) {
          animation-delay: 0.4s;
        }
        
        @keyframes bounce {
          0%, 100% { transform: translateY(0); opacity: 0.6; }
          50% { transform: translateY(-4px); opacity: 1; }
        }
      `}</style>
    </div>
  )
}