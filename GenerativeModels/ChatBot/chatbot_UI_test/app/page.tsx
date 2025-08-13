import { SalesForecastingChatbot } from "@/components/sales-forecasting-chatbot"

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Sales Forecasting Assistant</h1>
          <p className="text-lg text-gray-600">Ask me about your sales volume predictions using natural language</p>
        </div>
        <SalesForecastingChatbot />
      </div>
    </main>
  )
}
