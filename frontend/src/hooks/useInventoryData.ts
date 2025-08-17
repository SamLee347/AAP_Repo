"use client"

import { useState, useEffect } from "react"
import type { InventoryItem, Order } from "../App"

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000"

// Mock data as fallback
const mockInventory: InventoryItem[] = [
  {
    id: "101-elz",
    name: "Silky Creamy Donkey Steam Moisture Cream",
    category: "Cosmetics",
    brand: "Elizavecca",
    price: "$10.00",
    stock: 23,
    reserved: 3,
    image: "https://via.placeholder.com/40x40?text=Cream",
  },
  {
    id: "233-elz",
    name: "Gold CF-Nest 97% B-Jo Serum",
    category: "Cosmetics",
    brand: "Elizavecca",
    price: "$15.00",
    stock: 45,
    reserved: 8,
    image: "https://via.placeholder.com/40x40?text=Serum",
  },
]

const mockOrders: Order[] = [
  {
    id: "ORD-001",
    customer: "Beauty Store A",
    items: 15,
    total: "$450.00",
    status: "Processing",
    date: "2024-01-15",
  },
  {
    id: "ORD-002",
    customer: "Cosmetic Hub",
    items: 8,
    total: "$280.00",
    status: "Shipped",
    date: "2024-01-14",
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
          fetch(`${API_BASE_URL}/api/inventory`),
          fetch(`${API_BASE_URL}/api/orders`),
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
