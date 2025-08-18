"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const mockData = [
  { month: "Oct", actual: 35000, forecast: null },
  { month: "Nov", actual: 38000, forecast: null },
  { month: "Dec", actual: 42000, forecast: null },
  { month: "Jan", actual: null, forecast: 39000 },
  { month: "Feb", actual: null, forecast: 41000 },
  { month: "Mar", actual: null, forecast: 44000 },
]

export function ForecastChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Sales Trend & Forecast</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={mockData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip
                formatter={(value, name) => [
                  `${Number(value).toLocaleString()} units`,
                  name === "actual" ? "Actual" : "Forecast",
                ]}
              />
              <Line type="monotone" dataKey="actual" stroke="#2563eb" strokeWidth={2} dot={{ fill: "#2563eb" }} />
              <Line
                type="monotone"
                dataKey="forecast"
                stroke="#10b981"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: "#10b981" }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="flex justify-center gap-4 mt-2 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-600 rounded-full"></div>
            <span>Actual</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-600 rounded-full"></div>
            <span>Forecast</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
