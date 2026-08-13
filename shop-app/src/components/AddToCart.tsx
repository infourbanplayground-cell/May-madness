'use client'
import { useState } from 'react'
import { addToCart } from '@/lib/cart'

export default function AddToCart({ productId, stock }: { productId: string; stock: number }) {
  const [added, setAdded] = useState(false)

  if (stock <= 0) {
    return (
      <button disabled className="btn px-6 py-3 w-full sm:w-auto">
        SOLD OUT
      </button>
    )
  }

  return (
    <button
      className="btn px-6 py-3 w-full sm:w-auto"
      onClick={() => {
        addToCart(productId, 1)
        setAdded(true)
        setTimeout(() => setAdded(false), 1600)
      }}
    >
      {added ? 'ADDED ✓' : 'ADD TO CART'}
    </button>
  )
}
