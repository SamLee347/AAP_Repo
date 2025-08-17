import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp, TrendingDown, DollarSign, Package } from "lucide-react"

export function SalesMetrics() {
  const metrics = [
    {
      title: "Current Month",
      value: "42,350",
      change: "+12.5%",
      trend: "up" as const,
      icon: DollarSign,
    },
    {
      title: "Forecast Accuracy",
      value: "87.2%",
      change: "+2.1%",
      trend: "up" as const,
      icon: TrendingUp,
    },
    {
      title: "Units Predicted",
      value: "38,920",
      change: "-3.2%",
      trend: "down" as const,
      icon: Package,
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Key Metrics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {metrics.map((metric, index) => (
          <div key={index} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <metric.icon className="h-4 w-4 text-gray-500" />
              <span className="text-sm text-gray-600">{metric.title}</span>
            </div>
            <div className="text-right">
              <div className="font-semibold">{metric.value}</div>
              <div
                className={`text-xs flex items-center gap-1 ${
                  metric.trend === "up" ? "text-green-600" : "text-red-600"
                }`}
              >
                {metric.trend === "up" ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                {metric.change}
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
