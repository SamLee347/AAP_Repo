"use client"

import type React from "react"
import { useState } from "react"
import { MessageSquare } from 'lucide-react'

interface ChatMessage {
  type: "user" | "ai"
  content: string
}

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000"

export function ChatView() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage: ChatMessage = { type: "user", content: input }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      })

      if (response.ok) {
        const data = await response.json()
        const aiMessage: ChatMessage = { type: "ai", content: data.response }
        setMessages((prev) => [...prev, aiMessage])
      } else {
        throw new Error("API not available")
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        type: "ai",
        content: `I understand you're asking about: "${input}". I can help with inventory queries, stock analysis, and operational insights. (Note: Connect to Flask API for full functionality)`,
      }
      setMessages((prev) => [...prev, errorMessage])
    }

    setInput("")
    setLoading(false)
  }

  return (
    <div>
      <h2 className="mb-6 font-size-24 font-weight-600">
        AI Assistant
      </h2>
      <div className="card">
        <div className="chat-container">
          {messages.length === 0 ? (
            <div className="chat-empty">
              <MessageSquare size={48} color="#ced4da" className="chat-empty-icon" />
              <p>Ask me anything about your inventory, orders, or operations!</p>
            </div>
          ) : (
            <div className="chat-messages">
              {messages.map((msg, idx) => (
                <div key={idx} className={`message message-${msg.type}`}>
                  {msg.content}
                </div>
              ))}
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
          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading ? "..." : "Send"}
          </button>
        </form>
      </div>
    </div>
  )
}
