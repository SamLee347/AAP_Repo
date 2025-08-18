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
// Inventory model interface
export interface InventoryItem {
  ItemId: number
  Location: string | null
  Date: string
  ItemName: string
  ItemQuantity?: number | null
  ItemCategory?: string | null
  UnitsSold?: number | null
  Weight?: number | null
  Size?: string | null
  Priority: string
  Dispose?: boolean | null
}

// Order model interface
export interface Order {
  OrderId: number
  ItemId: number
  OrderQuantity: number
  Sales: number
  Price: number
  Discount: number
  Profit: number
  DateOrdered: string
  DateReceived: string
  CustomerSegment: string
  inventory_item?: InventoryItem
}

function App() {
  const [activeView, setActiveView] = useState("inventory")
  const [selectedItem, setSelectedItem] = useState<InventoryItem | Order | null>(null)
  const [searchTerm, setSearchTerm] = useState("")

  const { inventory, orders, loading } = useInventoryData()

  const handleItemSelect = (item: InventoryItem | Order) => {
    setSelectedItem(item)
  }

  // 🔑 Updated filtering logic
  const filteredInventory = inventory.filter((item) => {
    const term = searchTerm.toLowerCase()

    return (
      item.ItemId.toString().includes(term) ||
      (item.ItemCategory?.toLowerCase().includes(term) ?? false) ||
      (item.Priority?.toLowerCase().includes(term) ?? false) ||
      (item.Date?.toLowerCase().includes(term) ?? false)
    )
  })

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
              <OrdersView
                orders={orders}
                selectedItem={selectedItem}
                onItemSelect={handleItemSelect}
              />
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
