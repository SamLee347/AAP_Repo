"use client"
import type { Order, InventoryItem } from "../../App"

interface OrdersViewProps {
  orders: Order[]
  selectedItem: InventoryItem | Order | null
  onItemSelect: (item: Order) => void
}

export function OrdersView({ orders, selectedItem, onItemSelect }: OrdersViewProps) {
  return (
    <div>
      <div className="view-header">
        <h2 className="view-title">Orders</h2>
        <span className="badge badge-outline">Total: {orders.length}</span>
      </div>

      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Customer Segment</th>
              <th>Number of items</th>
              <th>Total Sales</th>
              <th>Profit</th>
              <th>Date Ordered</th>
              <th>Date Received</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr
                key={order.OrderId}
                className={selectedItem?.ItemId === order.OrderId ? "selected" : ""}
                onClick={() => onItemSelect(order)}
              >
                <td>
                  <code className="code-text">{order.OrderId}</code>
                </td>
                <td className="font-weight-500">{order.CustomerSegment}</td>
                <td>{order.OrderQuantity} items</td>
                <td className="font-weight-500">{order.Sales}</td>
                <td className="font-weight-500">{order.Profit}</td>
                {/* <td>
                  <span className={`badge ${order.status === "Shipped" ? "badge-success" : "badge-secondary"}`}>
                    {order.status}
                  </span>
                </td> */}
                <td className="font-size-14 color-muted">{order.DateOrdered}</td>
                <td className="font-size-14 color-muted">{order.DateReceived ? order.DateReceived : "N/A"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
