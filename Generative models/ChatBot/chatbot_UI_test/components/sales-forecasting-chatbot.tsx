"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Send, TrendingUp, Calendar, BarChart3 } from "lucide-react"
import { ForecastChart } from "./forecast-chart"
import { SalesMetrics } from "./sales-metrics"

interface Message {
  id: string
  type: "user" | "assistant"
  content: string
  timestamp: Date
  forecast?: ForecastData
}

interface ForecastData {
  period: string
  predicted_volume: number
  confidence: number
  trend: "up" | "down" | "stable"
  factors: string[]
}

export function SalesForecastingChatbot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "assistant",
      content:
        "Hello! I'm your sales forecasting assistant. You can ask me questions like 'What will our sales volume be next month?' or 'Show me Q4 predictions for product X'.",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleSendMessage = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    // Simulate NLP processing and forecasting
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: processNaturalLanguageQuery(input),
        timestamp: new Date(),
        forecast: generateMockForecast(input),
      }

      setMessages((prev) => [...prev, assistantMessage])
      setIsLoading(false)
    }, 2000)
  }

  const processNaturalLanguageQuery = (query: string): string => {
    // Mock NLP processing - in real implementation, this would use AI SDK
    const lowerQuery = query.toLowerCase()

    if (lowerQuery.includes("next month") || lowerQuery.includes("january")) {
      return "Based on historical data and current trends, here's the forecast for next month:"
    } else if (lowerQuery.includes("quarter") || lowerQuery.includes("q4")) {
      return "Here's the quarterly sales volume prediction:"
    } else if (lowerQuery.includes("product") || lowerQuery.includes("category")) {
      return "I've analyzed the product-specific sales patterns:"
    } else {
      return "Here's the sales volume forecast based on your query:"
    }
  }

  const generateMockForecast = (query: string): ForecastData => {
    // Mock forecast generation - in real implementation, this would use ML models
    return {
      period: "January 2025",
      predicted_volume: Math.floor(Math.random() * 50000) + 20000,
      confidence: Math.floor(Math.random() * 30) + 70,
      trend: ["up", "down", "stable"][Math.floor(Math.random() * 3)] as "up" | "down" | "stable",
      factors: ["Seasonal trends", "Historical performance", "Market conditions", "Product lifecycle stage"],
    }
  }

  return (
    <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Chat Interface */}
      <div className="lg:col-span-2">
        <Card className="h-[600px] flex flex-col">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Sales Forecasting Chat
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col">
            <ScrollArea className="flex-1 pr-4">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div key={message.id} className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[80%] rounded-lg p-3 ${
                        message.type === "user" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-900"
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      {message.forecast && (
                        <div className="mt-3 p-3 bg-white rounded border">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold text-gray-900">{message.forecast.period}</span>
                            <Badge variant={message.forecast.trend === "up" ? "default" : "secondary"}>
                              {message.forecast.trend}
                            </Badge>
                          </div>
                          <div className="text-2xl font-bold text-blue-600 mb-1">
                            {message.forecast.predicted_volume.toLocaleString()} units
                          </div>
                          <div className="text-sm text-gray-600">{message.forecast.confidence}% confidence</div>
                        </div>
                      )}
                      <div className="text-xs opacity-70 mt-1">{message.timestamp.toLocaleTimeString()}</div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 rounded-lg p-3">
                      <div className="flex items-center gap-2">
                        <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                        <span className="text-sm text-gray-600">Analyzing and forecasting...</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
            <div className="flex gap-2 mt-4">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about sales forecasts... (e.g., 'What will sales be next month?')"
                onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                disabled={isLoading}
              />
              <Button onClick={handleSendMessage} disabled={isLoading || !input.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sidebar with Charts and Metrics */}
      <div className="space-y-6">
        <SalesMetrics />
        <ForecastChart />

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Quick Forecasts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button
              variant="outline"
              className="w-full justify-start bg-transparent"
              onClick={() => setInput("What will sales be next month?")}
            >
              <Calendar className="h-4 w-4 mr-2" />
              Next Month
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start bg-transparent"
              onClick={() => setInput("Show me Q1 2025 predictions")}
            >
              <TrendingUp className="h-4 w-4 mr-2" />
              Q1 2025
            </Button>
            <Button
              variant="outline"
              className="w-full justify-start bg-transparent"
              onClick={() => setInput("Forecast by product category")}
            >
              <BarChart3 className="h-4 w-4 mr-2" />
              By Category
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
