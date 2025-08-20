"use client"

import { useState, useEffect } from "react"
import type { InventoryItem, Order } from "../App"

const API_BASE_URL = "http://localhost:5000"

// Mock data as fallback
const mockInventory: InventoryItem[] = [
  {
    ItemId: 101,
    ItemName: "Cool Gadget",
    ItemCategory: "Technology",
    Location: "A-1",
    Date: "2025-06-01",
    ItemQuantity: 100,
    UnitsSold: 50,
    Weight: 1.5,
    Size: "Small",
    Priority: "High",
    Dispose: false,
  },
  {
    ItemId: 102,
    ItemName: "Stylish Shirt",
    ItemCategory: "Clothing",
    Location: "A-2",
    Date: "2025-07-01",
    ItemQuantity: 200,
    UnitsSold: 100,
    Weight: 2.0,
    Size: "Medium",
    Priority: "Medium",
    Dispose: false,
  },
  {
    ItemId: 103,
    ItemName: "Cool Clothes",
    ItemCategory: "Clothing",
    Location: "C-6",
    Date: "2025-08-01",
    ItemQuantity: 150,
    UnitsSold: 75,
    Weight: 15.0,
    Size: "Large",
    Priority: "Low",
    Dispose: true,
  },
]

const mockOrders: Order[] = [
  {
    OrderId: 1001,
    ItemId: 101,
    OrderQuantity: 10,
    Sales: 5000,
    Price: 500,
    Discount: 50,
    Profit: 4500,
    DateOrdered: "2025-06-15",
    DateReceived: "2025-06-20",
    CustomerSegment: "Corporate",
  },
  {
    OrderId: 1002,
    ItemId: 102,
    OrderQuantity: 20,
    Sales: 2000,
    Price: 100,
    Discount: 20,
    Profit: 1980,
    DateOrdered: "2025-07-10",
    DateReceived: "2025-07-12",
    CustomerSegment: "Retail",
  },
  {
    OrderId: 1003,
    ItemId: 101,
    OrderQuantity: 5,
    Sales: 2500,
    Price: 500,
    Discount: 25,
    Profit: 2475,
    DateOrdered: "2025-08-05",
    DateReceived: "2025-08-10",
    CustomerSegment: "Wholesale",
  },
]

export function useInventoryData() {
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [inventoryRes, ordersRes] = await Promise.all([
          fetch(`${API_BASE_URL}/inventory`),
          fetch(`${API_BASE_URL}/orders`),
        ])

        if (inventoryRes.ok && ordersRes.ok) {
          const [inventoryData, ordersData] = await Promise.all([inventoryRes.json(), ordersRes.json()])
          setInventory(inventoryData)
          setOrders(ordersData)
        } else {
          throw new Error("API not available")
        }
      } catch (error) {
        console.log("Using mock data - Flask API not available")
        setInventory(mockInventory)
        setOrders(mockOrders)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  return { inventory, orders, loading }
}
