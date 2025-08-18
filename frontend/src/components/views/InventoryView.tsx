"use client"
import type { InventoryItem, Order } from "../../App"
import { Filter, MoreHorizontal } from 'lucide-react'

interface InventoryViewProps {
  inventory: InventoryItem[]
  selectedItem: InventoryItem | Order | null
  onItemSelect: (item: InventoryItem) => void
}

export function InventoryView({ inventory, selectedItem, onItemSelect }: InventoryViewProps) {
  return (
    <div>
      <div className="view-header">
        <h2 className="view-title">Inventory</h2>
        <div className="flex align-center gap-8">
          <span className="badge badge-outline">Total: {inventory.length}</span>
          <button className="btn btn-outline">
            <Filter size={16} />
            Filter
          </button>
        </div>
      </div>

      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Product ID</th>
              <th>Product Name</th>
              <th>Category</th>
              <th>Stock</th>
              <th>Total Units Sold</th>
              <th>Weight (kg)</th>
              <th>Size (cm)</th>
              <th>Priority</th>
              <th>Location</th>
              <th>Date Added</th>
              <th>Dispose?</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {inventory.map((item) => (
              <tr
                key={item.ItemId}
                className={selectedItem?.ItemId === item.ItemId ? "selected" : ""}
                onClick={() => onItemSelect(item)}
              >
                <td>
                  <code className="code-text">{item.ItemId}</code>
                </td>
                <td><h4>{item.ItemName}</h4></td>
                <td>
                  <span className="badge badge-outline">{item.ItemCategory}</span>
                </td>
                <td className="font-weight-500">{item.ItemQuantity ?? 0}</td>
                <td className="font-weight-500">{item.UnitsSold}</td>
                <td className="font-weight-500">{item.Weight} kg</td>
                <td className="font-weight-500">{item.Size} cm</td>
                <td className="font-weight-500">{item.Priority}</td>
                <td className="font-weight-500">{item.Location}</td>
                <td className="font-weight-500">{item.Date}</td>
                <td className="font-weight-500">
                  <input type="checkbox" checked={item.Dispose ?? false} readOnly />
                </td>
                <td>
                  <button className="btn padding-4-8" title="More actions">
                    <MoreHorizontal size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
