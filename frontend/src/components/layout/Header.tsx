"use client"
import { Building2, Search } from "lucide-react"

interface HeaderProps {
  searchTerm: string
  onSearchChange: (term: string) => void
}

export function Header({ searchTerm, onSearchChange }: HeaderProps) {
  return (
    <div className="header">
      <div className="header-content">
        <div className="header-title">
          <Building2 size={32} color="#0d6efd" />
          <h1>AI Inventory Management</h1>
        </div>
        <div className="search-container">
          <Search className="search-icon" size={16} />
          <input
            type="text"
            placeholder="Quick Search"
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="search-input"
          />
        </div>
      </div>
    </div>
  )
}
