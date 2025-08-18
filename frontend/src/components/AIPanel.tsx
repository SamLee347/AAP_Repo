"use client"

import { useState } from "react"
import type { InventoryItem, Order } from "../App"
import { Trash2, MapPin, TrendingUp, Tag } from 'lucide-react'

interface AIResult {
  recommendation?: string
  confidence?: number
  reasons?: string[]
  recommended_zone?: string
  factors?: string[]
  next_month?: number
  trend?: string
  category?: string
  attributes?: string[]
}

interface AIPanelProps {
  selectedItem: InventoryItem | Order
}

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000"

export function AIPanel({ selectedItem }: AIPanelProps) {
  const [activeTab, setActiveTab] = useState("disposal")
  const [results, setResults] = useState<Record<string, AIResult>>({})
  const [loading, setLoading] = useState<string | null>(null)

  const callAI = async (endpoint: string, tabKey: string) => {
    setLoading(tabKey)
    try {
      const response = await fetch(`${API_BASE_URL}/api/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_id: selectedItem.ItemId }),
      })

      if (response.ok) {
        const data = await response.json()
        setResults((prev) => ({ ...prev, [tabKey]: data }))
      } else {
        throw new Error("API not available")
      }
    } catch (error) {
      // Mock responses
      const mockResponses = {
        disposal: {
          recommendation: Math.random() > 0.7 ? "DISPOSE" : "KEEP",
          confidence: Math.floor(Math.random() * 30) + 70,
          reasons: ["Stock age: 45 days", "Low turnover rate", "Expiry approaching"],
        },
        storage: {
          recommended_zone: ["Zone A-1", "Zone B-3", "Zone C-2", "Cold Storage"][Math.floor(Math.random() * 4)],
          confidence: Math.floor(Math.random() * 25) + 75,
          factors: ["Temperature requirements", "Access frequency", "Space optimization"],
        },
        forecast: {
          next_month: Math.floor(Math.random() * 100) + 50,
          trend: Math.random() > 0.5 ? "increasing" : "stable",
          confidence: Math.floor(Math.random() * 20) + 80,
        },
        category: {
          category: ["Premium", "Standard", "Budget", "Seasonal"][Math.floor(Math.random() * 4)],
          confidence: Math.floor(Math.random() * 20) + 80,
          attributes: ["High demand", "Premium pricing", "Quality materials"],
        },
      }
      setResults((prev) => ({ ...prev, [tabKey]: mockResponses[tabKey as keyof typeof mockResponses] }))
    }
    setLoading(null)
  }

  const tabs = [
    { id: "disposal", label: "Disposal", icon: Trash2 },
    { id: "storage", label: "Storage", icon: MapPin },
    { id: "forecast", label: "Forecast", icon: TrendingUp },
    { id: "category", label: "Category", icon: Tag },
  ]

  return (
    <div className="ai-panel">


      <div className="tabs">
        <div className="tab-list">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                className={`tab-button ${activeTab === tab.id ? "active" : ""}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon size={12} />
                {tab.label}
              </button>
            )
          })}
        </div>

        {/* Tab Contents */}
        {tabs.map((tab) => (
          <div key={tab.id} className={`tab-content ${activeTab === tab.id ? "active" : ""}`}>
            <div className="card">
              <div className="card-header">
                <h4 className="card-title font-size-14">
                  {tab.label} {tab.id === "disposal" && "Prediction"}
                  {tab.id === "storage" && "Optimization"}
                  {tab.id === "forecast" && "Sales Forecast"}
                  {tab.id === "category" && "Categorization"}
                </h4>
              </div>
              <div className="card-body">
                <button
                  onClick={() =>
                    callAI(
                      `${tab.id === "disposal" ? "disposal-prediction" : tab.id === "storage" ? "storage-optimization" : tab.id === "forecast" ? "sales-forecast" : "categorization"}`,
                      tab.id,
                    )
                  }
                  disabled={loading === tab.id}
                  className="btn btn-primary mb-3 w-full"
                >
                  {loading === tab.id ? "Processing..." : `Analyze ${tab.label}`}
                </button>
                {results[tab.id] && (
                  <div>
                    {tab.id === "disposal" && (
                      <>
                        <span
                          className={`badge ${results[tab.id].recommendation === "DISPOSE" ? "badge-danger" : "badge-success"} mb-2`}
                        >
                          {results[tab.id].recommendation}
                        </span>
                        <div className="ai-result-confidence">
                          Confidence: {results[tab.id].confidence}%
                        </div>
                        <div className="ai-result-factors">
                          <div className="ai-result-factors-title">Factors:</div>
                          {results[tab.id].reasons?.map((reason, idx) => (
                            <div key={idx}>• {reason}</div>
                          ))}
                        </div>
                      </>
                    )}
                    {tab.id === "storage" && (
                      <>
                        <div className="ai-result-zone">
                          {results[tab.id].recommended_zone}
                        </div>
                        <div className="ai-result-confidence">
                          Confidence: {results[tab.id].confidence}%
                        </div>
                        <div className="ai-result-factors">
                          <div className="ai-result-factors-title">Factors:</div>
                          {results[tab.id].factors?.map((factor, idx) => (
                            <div key={idx}>• {factor}</div>
                          ))}
                        </div>
                      </>
                    )}
                    {tab.id === "forecast" && (
                      <div className="text-center-align">
                        <div className="ai-result-number">
                          {results[tab.id].next_month}
                        </div>
                        <div className="ai-result-label">Units next month</div>
                        <span
                          className={`badge ${results[tab.id].trend === "increasing" ? "badge-success" : "badge-secondary"} mb-2`}
                        >
                          {results[tab.id].trend}
                        </span>
                        <div className="ai-result-confidence">
                          Confidence: {results[tab.id].confidence}%
                        </div>
                      </div>
                    )}
                    {tab.id === "category" && (
                      <>
                        <span className="badge badge-outline mb-2">{results[tab.id].category}</span>
                        <div className="ai-result-confidence">
                          Confidence: {results[tab.id].confidence}%
                        </div>
                        <div className="ai-result-factors">
                          <div className="ai-result-factors-title">Attributes:</div>
                          {results[tab.id].attributes?.map((attr, idx) => (
                            <div key={idx}>• {attr}</div>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
