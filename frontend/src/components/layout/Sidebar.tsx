"use client"
import { Package, ShoppingCart, MessageSquare, FileText } from "lucide-react"

interface SidebarProps {
  activeView: string
  onViewChange: (view: string) => void
}

const navItems = [
  { id: "inventory", icon: Package, label: "Inventory" },
  { id: "orders", icon: ShoppingCart, label: "Orders" },
  { id: "chat", icon: MessageSquare, label: "AI Assistant" },
  { id: "reports", icon: FileText, label: "Reports" },
]

export function Sidebar({ activeView, onViewChange }: SidebarProps) {
  return (
    <div className="sidebar">
      {navItems.map((item) => {
        const Icon = item.icon
        return (
          <button
            key={item.id}
            className={`nav-button ${activeView === item.id ? "active" : ""}`}
            onClick={() => onViewChange(item.id)}
            title={item.label}
          >
            <Icon size={20} />
          </button>
        )
      })}
    </div>
  )
}
