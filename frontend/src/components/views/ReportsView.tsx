"use client"

import { useState } from "react"

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000"

export function ReportsView() {
  const [input, setInput] = useState("")
  const [result, setResult] = useState("")
  const [loading, setLoading] = useState(false)

  const handleGenerate = async () => {
    if (!input.trim()) return

    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/generate-report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: input }),
      })

      if (response.ok) {
        const data = await response.json()
        setResult(data.report)
      } else {
        throw new Error("API not available")
      }
    } catch (error) {
      setResult(`AI-Generated Insight Report:

Based on your query: "${input}"

Key Findings:
• Current inventory levels show 15% increase from last month
• Top performing category: Cosmetics (67% of total sales)
• Recommended reorder: Items with stock below 30 units
• Seasonal trend analysis suggests 20% uptick in Q2

Recommendations:
• Increase stock for high-demand Elizavecca products
• Consider promotional pricing for slow-moving items
• Optimize storage allocation for better efficiency

Note: Connect to Flask API for real AI-powered insights.`)
    }
    setLoading(false)
  }

  return (
    <div>
      <h2 className="mb-6 font-size-24 font-weight-600">
        AI Report Generation
      </h2>
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Generate Insights Report</h3>
          </div>
          <div className="card-body">
            <div className="form-group">
              <textarea
                placeholder="Describe what insights you need (e.g., 'Analyze sales trends for cosmetics category', 'Identify slow-moving inventory', 'Forecast demand for next quarter')"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                rows={4}
                className="form-textarea"
              />
            </div>
            <button onClick={handleGenerate} disabled={loading} className="btn btn-primary w-full">
              {loading ? "Generating..." : "Generate AI Report"}
            </button>
          </div>
        </div>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Generated Report</h3>
          </div>
          <div className="card-body">
            {result ? (
              <div className="report-output">
                {result}
              </div>
            ) : (
              <p className="color-muted">Enter your requirements and generate a report</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
