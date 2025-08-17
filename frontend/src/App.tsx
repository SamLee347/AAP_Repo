"use client"

import { useState } from "react"
import { Header } from "./components/layout/Header"
import { Sidebar } from "./components/layout/Sidebar"
import { InventoryView } from "./components/views/InventoryView"
import { OrdersView } from "./components/views/OrdersView"
import { ChatView } from "./components/views/ChatView"
import { ReportsView } from "./components/views/ReportsView"
import { AIPanel } from "./components/AIPanel"
import { useInventoryData } from "./hooks/useInventoryData"
import "./App.css"

// Types
export interface InventoryItem {
  id: string
  name: string
  category: string
  brand: string
  price: string
  stock: number
  reserved: number
  image?: string
}

export interface Order {
  id: string
  customer: string
  items: number
  total: string
  status: string
  date: string
}

function App() {
  const [activeView, setActiveView] = useState("inventory")
  const [selectedItem, setSelectedItem] = useState<InventoryItem | Order | null>(null)
  const [searchTerm, setSearchTerm] = useState("")

  const { inventory, orders, loading } = useInventoryData()

  const handleItemSelect = (item: InventoryItem | Order) => {
    setSelectedItem(item)
  }

  const filteredInventory = inventory.filter(
    (item) =>
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.id.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading inventory data...</p>
      </div>
    )
  }

  return (
    <div className="app">
      <Header searchTerm={searchTerm} onSearchChange={setSearchTerm} />

      <div className="main-layout">
        <Sidebar activeView={activeView} onViewChange={setActiveView} />

        <div className="content-layout">
          <div className="main-content">
            {activeView === "inventory" && (
              <InventoryView
                inventory={filteredInventory}
                selectedItem={selectedItem}
                onItemSelect={handleItemSelect}
              />
            )}

            {activeView === "orders" && (
              <OrdersView orders={orders} selectedItem={selectedItem} onItemSelect={handleItemSelect} />
            )}

            {activeView === "chat" && <ChatView />}

            {activeView === "reports" && <ReportsView />}
          </div>

          {selectedItem && (activeView === "inventory" || activeView === "orders") && (
            <AIPanel selectedItem={selectedItem} />
          )}
        </div>
      </div>
    </div>
  )
}

export default App
