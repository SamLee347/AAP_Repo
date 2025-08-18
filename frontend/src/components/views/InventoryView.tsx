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
              <th>SKU</th>
              <th>Product</th>
              <th>Category</th>
              <th>Stock</th>
              <th>Price</th>
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
                <td>
                  <div className="product-info">
                    
                    <div className="product-details">
                      <h4>{item.Priority}</h4>
                      <p>{item.Size}</p>
                      <p>{item.Weight} kg</p>
                    </div>
                  </div>
                </td>
                <td>
                  <span className="badge badge-outline">{item.ItemCategory}</span>
                </td>
                <td>
                  <div className="stock-info">
                    <div>{item.ItemQuantity} units</div>
                    <div>{item.UnitsSold} reserved</div>
                    <div>{item.Dispose ? "Yes" : "No"}</div>
                  </div>
                </td>
                <td className="font-weight-500">{item.Date}</td>
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
