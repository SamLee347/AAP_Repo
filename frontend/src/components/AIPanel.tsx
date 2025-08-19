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

const ENDPOINT_MAP = {
  disposal: "disposal-prediction",
  storage: "predictLocation",
  forecast: "sales-forecast",
  category: "categorization"
} as const;

interface AIPanelProps {
  selectedItem: InventoryItem | Order
}

const API_BASE_URL = "http://localhost:5000"

export function AIPanel({ selectedItem }: AIPanelProps) {
  const [activeTab, setActiveTab] = useState("disposal")
  const [results, setResults] = useState<Record<string, AIResult>>({})
  const [loading, setLoading] = useState<string | null>(null)

  const callAI = async (tabKey: keyof typeof ENDPOINT_MAP) => {
  setLoading(tabKey);
  try {
    const response = await fetch(`${API_BASE_URL}/${ENDPOINT_MAP[tabKey]}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_id: selectedItem.ItemId }),
    });
    console.log("Calling AI endpoint:", ENDPOINT_MAP[tabKey], "with item_id:", selectedItem.ItemId);
    console.log("Response status:", response.status);

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    
    const data = await response.json();
    setResults(prev => ({ ...prev, [tabKey]: data })); // Direct use now
    
  } catch (error) {
    console.error("Prediction error:", error);
  } finally {
    setLoading(null);
  }
};
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
                  onClick={() => callAI(tab.id as keyof typeof ENDPOINT_MAP)}
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
                          className={`badge ${
                            results[tab.id].recommendation === "DISPOSE"
                              ? "badge-danger"
                              : results[tab.id].recommendation === "KEEP"
                              ? "badge-success"
                            : "badge-warning"  // For UNCERTAIN
                        } mb-2`}
                      >{results[tab.id].recommendation}
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
                          {results[tab.id].recommendation}
                        </div>
                        <div className="ai-result-confidence">
                          Confidence: {results[tab.id].confidence}%
                        </div>
                        <div className="ai-result-factors">
                          <div className="ai-result-factors-title">Factors:</div>
                          {results[tab.id].reasons?.map((factor, idx) => (
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
                    // In your AIPanel component, update the categorization section:
                    {tab.id === "category" && (
                      <>
                        <span className="badge badge-outline mb-2">
                          {results[tab.id]?.category || "Unknown"}
                        </span>
                        <div className="ai-result-confidence">
                          Confidence: {results[tab.id]?.confidence?.toFixed(1) || "N/A"}%
                        </div>
                        <div className="ai-result-factors">
                          <div className="ai-result-factors-title">Attributes:</div>
                          {results[tab.id]?.attributes?.map((attr, idx) => (
                            <div key={idx}>• {attr}</div>
                          )) || <div>No attributes available</div>}
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
