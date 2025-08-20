"use client"

import { useState, useEffect } from "react"
import type { InventoryItem, Order } from "../App"

const API_BASE_URL = "http://localhost:5000"

// Mock data as fallback
const mockInventory: InventoryItem[] = [
  {
    id: "101",
    name: "Cool Gadget",
    category: "Technology",
    brand: "TechCorp",
    price: "$500.00",
    stock: 100,
    reserved: 10,
    image: "https://via.placeholder.com/40x40?text=Gadget",
  },
  {
    id: "102",
    name: "Stylish Shirt",
    category: "Clothing",
    brand: "FashionInc",
    price: "$100.00",
    stock: 200,
    reserved: 20,
    image: "https://via.placeholder.com/40x40?text=Shirt",
  },
  {
    id: "103",
    name: "Cool Clothes",
    category: "Clothing",
    brand: "StyleCo",
    price: "$75.00",
    stock: 150,
    reserved: 5,
    image: "https://via.placeholder.com/40x40?text=Clothes",
  },
]

const mockOrders: Order[] = [
  {
    id: "1001",
    customer: "Corporate Client A",
    items: 10,
    total: "$5000.00",
    status: "Processing",
    date: "2025-06-15",
  },
  {
    id: "1002",
    customer: "Retail Store B",
    items: 20,
    total: "$2000.00",
    status: "Shipped",
    date: "2025-07-10",
  },
  {
    id: "1003",
    customer: "Wholesale Client C",
    items: 5,
    total: "$2500.00",
    status: "Delivered",
    date: "2025-08-05",
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
        // setInventory(mockInventory)
        // setOrders(mockOrders)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  return { inventory, orders, loading }
}
